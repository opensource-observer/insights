import json
from pathlib import Path
from typing import List, Dict, Any
from .settings import PROJECT_ROOT, GEMINI_API_KEY, OSO_API_KEY, GITHUB_TOKEN, GEMINI_MODEL, OUTPUT_DIR
from .prompts.summary_prompts import SUMMARY_PROMPT


class ConfigManager:
    def __init__(self, config_file_name: str = "pipeline_config.json"):
        self.config_file_path = PROJECT_ROOT / config_file_name
        self.config_data = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """
        Loads configuration from a JSON file, merging it with defaults.
        If the file doesn't exist or is invalid, creates a default one.
        Values in the JSON file override default values.
        """
        default_config = self._get_default_config()

        if self.config_file_path.exists():
            with open(self.config_file_path, 'r') as f:
                try:
                    loaded_config = json.load(f)
                    # Merge: loaded_config values override default_config values
                    merged_config = {**default_config, **loaded_config}
                    return merged_config
                except json.JSONDecodeError:
                    print(f"Warning: Could not decode JSON from {self.config_file_path}. Using full default config.")                
                    return default_config
        else:
            print(f"Config file not found at {self.config_file_path}. Creating and using default config.")
            self.save_config(default_config) 
            return default_config

    def _get_default_config(self) -> Dict[str, Any]:
        """Returns the default configuration dictionary."""
        return {
            "output_dir": str(OUTPUT_DIR),
            "gemini_model": GEMINI_MODEL,
            "summary_prompt_template": SUMMARY_PROMPT,
            "test_mode": False,
            "test_mode_limit": 5,
            "batch_size_summaries": 10
        }

    def save_config(self, config_data: Dict[str, Any] = None):
        """Saves the current configuration to the JSON file."""
        data_to_save = config_data if config_data else self.config_data
        with open(self.config_file_path, 'w') as f:
            json.dump(data_to_save, f, indent=4)
        print(f"Configuration saved to {self.config_file_path}")

    def get(self, key: str, default: Any = None) -> Any:
        """Gets a configuration value by key."""
        return self.config_data.get(key, default)

    def set(self, key: str, value: Any):
        """Sets a configuration value and saves the config."""
        if key in ["gemini_api_key", "oso_api_key", "github_token"]:
            print(f"Warning: Attempted to set API key '{key}' in config file. API keys should be managed via .env file.")
            return
        self.config_data[key] = value
        self.save_config()

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
        return self.get("test_mode", False)

    def get_test_mode_limit(self) -> int:
        """Gets the limit for test mode."""
        return self.get("test_mode_limit", 5)

    def get_output_dir(self) -> Path:
        return Path(self.get("output_dir", str(OUTPUT_DIR)))

    def get_batch_size_summaries(self) -> int:
        return self.get("batch_size_summaries", 10)

    def get_summary_prompt_template(self) -> str:
        return self.get("summary_prompt_template", "")

if __name__ == "__main__":
    # Example usage:
    config_manager = ConfigManager()
    print(f"Output Directory: {config_manager.get_output_dir()}")
    print(f"Test Mode: {config_manager.is_test_mode()}")