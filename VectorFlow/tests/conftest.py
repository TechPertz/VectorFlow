import os
import sys
import pytest
from dotenv import load_dotenv

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

load_dotenv()

def pytest_configure(config):
    """Register custom markers to allow running specific test types"""
    config.addinivalue_line("markers", "unit: mark a test as a unit test")
    config.addinivalue_line("markers", "integration: mark a test as an integration test")
    config.addinivalue_line("markers", "mock: mark a test as using mock data")
    config.addinivalue_line("markers", "real: mark a test as using real API calls")
