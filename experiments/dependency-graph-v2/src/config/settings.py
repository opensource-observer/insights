import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API Keys
OSO_API_KEY = os.getenv("OSO_API_KEY")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "output"

# Create directories if they don't exist
DATA_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

# GitHub API settings
GITHUB_HEADERS = {"Authorization": f"token {GITHUB_TOKEN}"}

# Gemini model settings
GEMINI_MODEL = "gemini-2.0-flash"

# Pipeline configuration
TEST_MODE = False
TEST_MODE_LIMIT = 5