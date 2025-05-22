import json
import pandas as pd
import time
from dataclasses import dataclass, asdict
from typing import List, Type, TypeVar, Union, Dict, Any
import google.generativeai as genai
from ..config.config_manager import ConfigManager

# Define generic type for output classes
T = TypeVar(
    'T',
    bound=Union['SummaryOutput']
)

@dataclass
class SummaryOutput:
    summary: str

class AIService:
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.api_key = self.config_manager.get_gemini_api_key() 
        self.model_name = self.config_manager.get("gemini_model")
        
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in configuration.")
        if not self.model_name:
            raise ValueError("GEMINI_MODEL not found in configuration.")
            
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(self.model_name)
        self.request_count = 0
        self.start_time = time.time()

    def __del__(self):
        """Cleanup method to properly close gRPC connections."""
        try:
            # Force cleanup of any pending gRPC operations
            if hasattr(self, 'model'):
                del self.model
            # Reset the genai configuration
            genai.reset_session()
        except Exception as e:
            print(f"Warning: Error during cleanup: {e}")

    def _rate_limit_control(self):
        """Basic rate limiting: 60 requests per minute for flash models."""
        self.request_count += 1
        elapsed_time = time.time() - self.start_time
        if elapsed_time < 60 and self.request_count > 55: # Slight safety margin
            sleep_time = 60 - elapsed_time
            print(f"Rate limit approaching. Sleeping for {sleep_time:.2f} seconds.")
            time.sleep(sleep_time)
            self.request_count = 0
            self.start_time = time.time()
        elif elapsed_time >= 60:
            self.request_count = 0
            self.start_time = time.time()

    def execute_query(self, prompt: str, output_class: Type[T]) -> T:
        """Execute a query against the Gemini API and parse the response."""
        self._rate_limit_control()
        print(f"\nSending prompt to Gemini (model: {self.model_name})...")

        try:
            response = self.model.generate_content(prompt)
        except Exception as e:
            print(f"Error calling Gemini API: {e}")
            # Fallback for errors
            if output_class is SummaryOutput:
                return SummaryOutput(summary="Error generating summary.")
            raise

        try:
            text = response.text.strip()
            # Try to find JSON block, robustly
            json_str = None
            if output_class is BatchClassificationOutput: # Expects a list
                 start_brace = text.find("[")
                 end_brace = text.rfind("]") + 1 # Add 1 to include the closing bracket
            else: # Expects an object
                start_brace = text.find("{")
                end_brace = text.rfind("}") + 1 # Add 1 to include the closing brace

            if start_brace != -1 and end_brace > start_brace:
                json_str = text[start_brace:end_brace]
                data = json.loads(json_str)
            else:
                print("No valid JSON found in response.")
                raise ValueError("No JSON object/array found in response")

            if output_class is SummaryOutput:
                return SummaryOutput(summary=data.get("summary", "Summary not found in response."))
            raise ValueError(f"Unknown output class: {output_class}")

        except (json.JSONDecodeError, ValueError) as e:
            print(f"Error processing Gemini response: {e}. Raw text: '{response.text[:300]}...'")
            if output_class is SummaryOutput:
                return SummaryOutput(summary="Failed to parse summary from response.")
            raise

    def make_summary(self, readme_md: str) -> SummaryOutput:
        """Generate a summary of the project based on its README."""
        if not readme_md or not readme_md.strip():
            return SummaryOutput(summary="This appears to be an empty repository without a README file.")
        
        prompt_template = self.config_manager.get_summary_prompt_template()
        prompt = prompt_template.format(readme_md=readme_md)
        return self.execute_query(prompt, SummaryOutput)


if __name__ == '__main__':
    # Example Usage
    # Example Usage:
    # cfg_manager = ConfigManager() 
    # ai_service = AIService(config_manager=cfg_manager)
    # print("AIService initialized for standalone testing if needed.")
    pass
