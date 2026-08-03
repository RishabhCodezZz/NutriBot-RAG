"""Runs before any sibling test module is collected/imported, so config.py
and rag.py (which need GEMINI_API_KEY at import time) don't blow up in an
environment with no real key. No network calls happen just from importing -
genai.configure() only stores the string locally.
"""
import os

os.environ.setdefault("GEMINI_API_KEY", "test-dummy-key-for-pytest")
