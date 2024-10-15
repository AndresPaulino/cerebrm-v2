import os
from dotenv import load_dotenv

# Print current working directory
print(f"Current working directory: {os.getcwd()}")

# Try to load the .env file
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
print(f"Looking for .env file at: {env_path}")

if os.path.exists(env_path):
    print(".env file found")
    load_dotenv(env_path)
else:
    print(".env file not found")

# Print all environment variables
print("Environment variables:")
for key, value in os.environ.items():
    print(f"{key}: {value}")