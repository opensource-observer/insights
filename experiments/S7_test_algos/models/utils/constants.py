"""
Some constants and path management helpers
"""
from pathlib import Path

# Base directories
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent

# Data directories
DATA_DIR = PROJECT_ROOT / 'data' / 'onchain_testing'
WEIGHTS_DIR = PROJECT_ROOT / 'weights'

# Default paths
DEFAULT_CONFIG = WEIGHTS_DIR / 'onchain_builders_testing.yaml'

# Ensure required directories exist
DATA_DIR.mkdir(exist_ok=True)
WEIGHTS_DIR.mkdir(exist_ok=True)

def validate_paths() -> None:
    """Validate that all required files and directories exist."""
    required_paths = [
        (DEFAULT_CONFIG, "Config file"),
    ]
    
    missing = []
    for path, desc in required_paths:
        if not path.exists():
            missing.append(f"{desc} not found at: {path}")
    
    if missing:
        raise FileNotFoundError("\n".join(missing)) 