from pathlib import Path
from .settings import (
    GEMINI_API_KEY, 
    OSO_API_KEY, 
    GITHUB_TOKEN, 
    GEMINI_MODEL, 
    OUTPUT_DIR,
    TEST_MODE,
    TEST_MODE_LIMIT
)


class ConfigManager:
    def __init__(self):
        pass

    # --- API Key Getters ---
    def get_gemini_api_key(self) -> str:
        """Gets the Gemini API key directly from settings (environment)."""
        return GEMINI_API_KEY

    def get_oso_api_key(self) -> str:
        """Gets the OSO API key directly from settings (environment)."""
        return OSO_API_KEY

    def get_github_token(self) -> str:
        """Gets the GitHub token directly from settings (environment)."""
        return GITHUB_TOKEN

    def is_test_mode(self) -> bool:
        """Checks if test mode is enabled."""
        return TEST_MODE

    def get_test_mode_limit(self) -> int:
        """Gets the limit for test mode."""
        return TEST_MODE_LIMIT

    def get_output_dir(self) -> Path:
        """Gets the output directory path."""
        return OUTPUT_DIR


    def get_gemini_model(self) -> str:
        """Gets the Gemini model name."""
        return GEMINI_MODEL


if __name__ == "__main__":
    # Example usage:
    config_manager = ConfigManager()
    print(f"Output Directory: {config_manager.get_output_dir()}")
    print(f"Test Mode: {config_manager.is_test_mode()}")
