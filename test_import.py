# test_import.py
import os
print("Current working directory:", os.getcwd())
print("Contents of current directory:", os.listdir())
print("This is a test print")
print("Starting test_import.py")
from app.core.config import settings
print(f"Imported settings in test file: {settings}")