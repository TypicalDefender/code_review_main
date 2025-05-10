#!/bin/bash

# Run all tests for the git-integration service

# Set up Python path
export PYTHONPATH=$PYTHONPATH:$(pwd)/src

# Run the tests
python -m unittest discover -s tests
