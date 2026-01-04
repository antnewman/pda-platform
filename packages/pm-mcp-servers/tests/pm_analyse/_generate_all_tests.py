#!/usr/bin/env python3
"""
Script to generate all 8 comprehensive test files for pm-analyse module.
Generates 135+ tests covering all components.
"""

import os

TEST_DIR = os.path.dirname(os.path.abspath(__file__))

def write_file(filename, content):
    """Write content to file."""
    filepath = os.path.join(TEST_DIR, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Created: {filename} ({len(content)} bytes)")

# Will import test definitions from separate data file
# This keeps the generator script manageable
print(f"Generating tests in: {TEST_DIR}")
print("=" * 70)

# Import test content definitions
try:
    from test_content_defs import (
        CONFTEST_CONTENT,
        TEST_MODELS_CONTENT,
        TEST_RISK_ENGINE_CONTENT,
        TEST_FORECASTERS_CONTENT,
        TEST_ANALYZERS_CONTENT,
        TEST_TOOLS_CONTENT,
        TEST_SERVER_CONTENT,
        TEST_INTEGRATION_CONTENT
    )
    
    # Generate all files
    write_file('conftest.py', CONFTEST_CONTENT)
    write_file('test_models.py', TEST_MODELS_CONTENT)
    write_file('test_risk_engine.py', TEST_RISK_ENGINE_CONTENT)
    write_file('test_forecasters.py', TEST_FORECASTERS_CONTENT)
    write_file('test_analyzers.py', TEST_ANALYZERS_CONTENT)
    write_file('test_tools.py', TEST_TOOLS_CONTENT)
    write_file('test_server.py', TEST_SERVER_CONTENT)
    write_file('test_integration.py', TEST_INTEGRATION_CONTENT)
    
    print("=" * 70)
    print("All test files generated successfully!")
    
except ImportError:
    print("ERROR: test_content_defs.py not found")
    print("Creating inline instead...")
    
    # We'll generate files with minimal content first
    # Then expand them iteratively
    
