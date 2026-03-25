#!/usr/bin/env python
"""
Test runner for Myths and Legends API.

Runs pytest with configured options.
"""
import sys
import pytest

if __name__ == "__main__":
    # Pass command line arguments to pytest
    sys.exit(pytest.main(sys.argv[1:]))
