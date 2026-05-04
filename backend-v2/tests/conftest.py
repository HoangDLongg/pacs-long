"""
tests/conftest.py — Pytest configuration & shared fixtures
"""
import sys
import os

# Thêm backend-v2 vào PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
