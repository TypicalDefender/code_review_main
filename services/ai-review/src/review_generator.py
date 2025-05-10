"""
Review Generator for OpenCodeReview.

This module generates code reviews using LLMs based on code changes and analysis results.
"""

import logging
from typing import Dict, Any, List, Optional

from .llm.llm_client import LLMClient
from .prompts.prompt_manager import PromptManager
from .suggestions.suggestion_generator import SuggestionGenerator
from ..common.config import Config
from ..common.models import CodeChange, AnalysisResult, ReviewComment

logger = logging.getLogger(__name__)

class ReviewGenerator:
    """Generates code reviews using LLMs."""

    def __init__(
        self,
        config: Config,
        llm_client: LLMClient,
        prompt_manager: PromptManager,
        suggestion_generator: SuggestionGenerator,
    ):
        """Initialize the review generator.

        Args:
            config: The system configuration
            llm_client: The LLM client for generating reviews
            prompt_manager: The prompt manager for creating LLM prompts
            suggestion_generator: The suggestion generator for creating code suggestions
        """
        self.config = config
        self.llm_client = llm_client
        self.prompt_manager = prompt_manager
        self.suggestion_generator = suggestion_generator
        
        # Get configuration values
        self.model_name = config.get("ai.model.name", "gpt-4")
        self.temperature = config.get("ai.model.temperature", 0.2)
        self.max_tokens = config.get("ai.model.max_tokens", 4000)
        self.review_profile = config.get("reviews.profile", "Balanced")

    async def generate_review(
        self,
        code_changes: List[CodeChange],
        analysis_results: List[AnalysisResult],
        repository_context: Dict[str, Any],
    ) -> List[ReviewComment]:
        """Generate a code review for the given changes.

        Args:
            code_changes: The code changes to review
            analysis_results: The results of static analysis
            repository_context: Additional context about the repository

        Returns:
            A list of review comments
        """
        logger.info(f"Generating review for {len(code_changes)} changes with {len(analysis_results)} analysis results")
        
        # Group changes by file for context
        changes_by_file = self._group_changes_by_file(code_changes)
        
        # Group analysis results by file
        analysis_by_file = self._group_analysis_by_file(analysis_results)
        
        # Generate review comments for each file
        all_comments = []
        for file_path, file_changes in changes_by_file.items():
            file_analysis = analysis_by_file.get(file_path, [])
            
            # Get file-specific review instructions
            instructions = self._get_review_instructions(file_path, repository_context)
            
            # Generate comments for this file
            file_comments = await self._generate_file_review(
                file_path, file_changes, file_analysis, instructions, repository_context
            )
            
            all_comments.extend(file_comments)
        
        # Generate an overall summary comment
        if all_comments:
            summary_comment = await self._generate_summary(
                code_changes, analysis_results, all_comments, repository_context
            )
            all_comments.insert(0, summary_comment)
        
        return all_comments

    def _group_changes_by_file(self, code_changes: List[CodeChange]) -> Dict[str, List[CodeChange]]:
        """Group code changes by file path.

        Args:
            code_changes: The code changes to group

        Returns:
            A dictionary mapping file paths to lists of changes
        """
        changes_by_file = {}
        for change in code_changes:
            if change.file_path not in changes_by_file:
                changes_by_file[change.file_path] = []
            changes_by_file[change.file_path].append(change)
        return changes_by_file

    def _group_analysis_by_file(self, analysis_results: List[AnalysisResult]) -> Dict[str, List[AnalysisResult]]:
        """Group analysis results by file path.

        Args:
            analysis_results: The analysis results to group

        Returns:
            A dictionary mapping file paths to lists of analysis results
        """
        analysis_by_file = {}
        for result in analysis_results:
            if result.file_path not in analysis_by_file:
                analysis_by_file[result.file_path] = []
            analysis_by_file[result.file_path].append(result)
        return analysis_by_file

    def _get_review_instructions(self, file_path: str, repository_context: Dict[str, Any]) -> str:
        """Get review instructions for a specific file.

        Args:
            file_path: The path of the file
            repository_context: Additional context about the repository

        Returns:
            Review instructions for the file
        """
        # Get path-specific instructions from config
        path_instructions = self.config.get_path_specific("reviews.instructions.paths", file_path)
        if path_instructions:
            return path_instructions
        
        # Fall back to default instructions
        return self.config.get("reviews.instructions.default", "")

    async def _generate_file_review(
        self,
        file_path: str,
        changes: List[CodeChange],
        analysis_results: List[AnalysisResult],
        instructions: str,
        repository_context: Dict[str, Any],
    ) -> List[ReviewComment]:
        """Generate review comments for a specific file.

        Args:
            file_path: The path of the file
            changes: The changes to the file
            analysis_results: The analysis results for the file
            instructions: Review instructions for the file
            repository_context: Additional context about the repository

        Returns:
            A list of review comments for the file
        """
        logger.info(f"Generating review for file: {file_path}")
        
        # Prepare the context for the LLM
        context = self._prepare_file_context(file_path, changes, analysis_results, repository_context)
        
        # Generate the prompt
        prompt = self.prompt_manager.create_file_review_prompt(
            file_path=file_path,
            changes=changes,
            analysis_results=analysis_results,
            instructions=instructions,
            profile=self.review_profile,
            context=context,
        )
        
        # Generate the review using the LLM
        response = await self.llm_client.generate(
            prompt=prompt,
            model=self.model_name,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )
        
        # Parse the response into review comments
        comments = self._parse_review_response(response, file_path)
        
        # Generate code suggestions for each comment
        for comment in comments:
            if comment.suggestion_needed:
                suggestion = await self.suggestion_generator.generate_suggestion(
                    file_path=file_path,
                    code_changes=changes,
                    comment=comment,
                    repository_context=repository_context,
                )
                comment.suggestion = suggestion
        
        return comments

    def _prepare_file_context(
        self,
        file_path: str,
        changes: List[CodeChange],
        analysis_results: List[AnalysisResult],
        repository_context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Prepare the context for a file review.

        Args:
            file_path: The path of the file
            changes: The changes to the file
            analysis_results: The analysis results for the file
            repository_context: Additional context about the repository

        Returns:
            A dictionary containing the context for the file review
        """
        # Get file type
        file_extension = file_path.split(".")[-1] if "." in file_path else ""
        
        # Get repository structure
        repo_structure = repository_context.get("structure", {})
        
        # Get file history if available
        file_history = repository_context.get("file_history", {}).get(file_path, [])
        
        # Get related files
        related_files = self._find_related_files(file_path, repo_structure)
        
        return {
            "file_type": file_extension,
            "file_history": file_history,
            "related_files": related_files,
            "repository_structure": repo_structure,
        }

    def _find_related_files(self, file_path: str, repo_structure: Dict[str, Any]) -> List[str]:
        """Find files related to the given file.

        Args:
            file_path: The path of the file
            repo_structure: The repository structure

        Returns:
            A list of related file paths
        """
        # This is a simplified implementation
        # In a real system, this would use more sophisticated methods to find related files
        related_files = []
        
        # Files in the same directory
        directory = "/".join(file_path.split("/")[:-1])
        if directory in repo_structure:
            related_files.extend([f"{directory}/{f}" for f in repo_structure[directory]])
        
        # Limit the number of related files
        max_related = self.config.get("ai.context.max_related_files", 5)
        return related_files[:max_related]

    def _parse_review_response(self, response: str, file_path: str) -> List[ReviewComment]:
        """Parse the LLM response into review comments.

        Args:
            response: The LLM response
            file_path: The path of the file

        Returns:
            A list of review comments
        """
        # This is a simplified implementation
        # In a real system, this would use more sophisticated parsing
        
        comments = []
        lines = response.strip().split("\n")
        
        current_comment = None
        for line in lines:
            if line.startswith("COMMENT:"):
                # Save the previous comment if it exists
                if current_comment:
                    comments.append(current_comment)
                
                # Start a new comment
                current_comment = ReviewComment(
                    file_path=file_path,
                    line_number=None,
                    content="",
                    severity="info",
                    suggestion_needed=False,
                )
            elif line.startswith("LINE:") and current_comment:
                try:
                    current_comment.line_number = int(line.replace("LINE:", "").strip())
                except ValueError:
                    pass
            elif line.startswith("SEVERITY:") and current_comment:
                current_comment.severity = line.replace("SEVERITY:", "").strip().lower()
            elif line.startswith("SUGGESTION:") and current_comment:
                current_comment.suggestion_needed = line.replace("SUGGESTION:", "").strip().lower() == "yes"
            elif current_comment:
                current_comment.content += line + "\n"
        
        # Add the last comment
        if current_comment:
            comments.append(current_comment)
        
        # Clean up comment content
        for comment in comments:
            comment.content = comment.content.strip()
        
        return comments

    async def _generate_summary(
        self,
        code_changes: List[CodeChange],
        analysis_results: List[AnalysisResult],
        comments: List[ReviewComment],
        repository_context: Dict[str, Any],
    ) -> ReviewComment:
        """Generate a summary comment for the entire review.

        Args:
            code_changes: All code changes
            analysis_results: All analysis results
            comments: All generated comments
            repository_context: Additional context about the repository

        Returns:
            A summary review comment
        """
        logger.info("Generating review summary")
        
        # Count issues by severity
        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
        for comment in comments:
            if comment.severity in severity_counts:
                severity_counts[comment.severity] += 1
        
        # Generate the prompt
        prompt = self.prompt_manager.create_summary_prompt(
            code_changes=code_changes,
            analysis_results=analysis_results,
            comments=comments,
            severity_counts=severity_counts,
            repository_context=repository_context,
        )
        
        # Generate the summary using the LLM
        response = await self.llm_client.generate(
            prompt=prompt,
            model=self.model_name,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )
        
        # Create a summary comment
        return ReviewComment(
            file_path=None,  # Summary applies to the entire PR
            line_number=None,
            content=response.strip(),
            severity="info",
            suggestion_needed=False,
        )
