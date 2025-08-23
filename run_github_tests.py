#!/usr/bin/env python3
"""
Test runner script for CI environments
"""
import sys
import os
from pathlib import Path

# Add project paths to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'src'))
sys.path.insert(0, str(project_root / 'webapp'))

if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main(["tests/", "-v"]))