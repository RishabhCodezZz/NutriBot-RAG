"""Runs before any sibling test module is collected/imported, so config.py
and rag.py (which need OLLAMA_API_KEY at import time to build the Ollama
client, and GEMINI_API_KEY for the eval judge) don't blow up in an
environment with no real keys. No network calls happen just from importing -
building an ollama.Client / calling genai.configure() only stores strings
locally.
"""
import os

os.environ.setdefault("GEMINI_API_KEY", "test-dummy-key-for-pytest")
os.environ.setdefault("OLLAMA_API_KEY", "test-dummy-key-for-pytest")
