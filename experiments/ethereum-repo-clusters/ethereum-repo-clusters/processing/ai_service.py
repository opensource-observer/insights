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
    bound=Union['SummaryOutput', 'ClassificationOutput', 'BatchClassificationOutput']
)

@dataclass
class SummaryOutput:
    summary: str

@dataclass
class ClassificationOutput:
    assigned_tag: str
    reason: str

@dataclass
class BatchClassificationOutput:
    classifications: List[ClassificationOutput]


class AIService:
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.api_key = self.config_manager.get_gemini_api_key() # Use specific getter
        self.model_name = self.config_manager.get("gemini_model") # Model name can stay in JSON config
        
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in configuration.")
        if not self.model_name:
            raise ValueError("GEMINI_MODEL not found in configuration.")
            
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(self.model_name)
        self.request_count = 0
        self.start_time = time.time()

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
            if output_class is ClassificationOutput:
                return ClassificationOutput(assigned_tag="Error", reason="API call failed.")
            if output_class is BatchClassificationOutput:
                return BatchClassificationOutput(classifications=[])
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
            if output_class is ClassificationOutput: # For single classification
                return ClassificationOutput(
                    assigned_tag=data.get("assigned_tag", "Other"),
                    reason=data.get("reason", "Could not classify project from response.")
                )
            if output_class is BatchClassificationOutput: # For batch classification
                classifications_data = data # data is already the list
                parsed_classifications = [
                    ClassificationOutput(
                        assigned_tag=item.get("assigned_tag", "Other"),
                        reason=item.get("reason", "Could not classify.")
                    ) for item in classifications_data
                ]
                return BatchClassificationOutput(classifications=parsed_classifications)

            raise ValueError(f"Unknown output class: {output_class}")

        except (json.JSONDecodeError, ValueError) as e:
            print(f"Error processing Gemini response: {e}. Raw text: '{response.text[:300]}...'")
            if output_class is SummaryOutput:
                return SummaryOutput(summary="Failed to parse summary from response.")
            if output_class is ClassificationOutput:
                return ClassificationOutput(assigned_tag="Other", reason="Failed to parse classification.")
            if output_class is BatchClassificationOutput:
                 # Return empty list of classifications for the batch
                return BatchClassificationOutput(classifications=[])
            raise

    def make_summary(self, readme_md: str) -> SummaryOutput:
        """Generate a summary of the project based on its README."""
        if not readme_md or not readme_md.strip():
            return SummaryOutput(summary="This appears to be an empty repository without a README file.")
        
        prompt_template = self.config_manager.get_summary_prompt_template()
        prompt = prompt_template.format(readme_md=readme_md)
        return self.execute_query(prompt, SummaryOutput)

    def classify_projects_batch_for_persona(
        self,
        project_data_batch: List[Dict[str, Any]], # Changed from summaries: List[str]
        persona: Dict[str, Any]
    ) -> List[ClassificationOutput]:
        """
        Classify multiple projects at once for a specific persona using their summaries and metadata.
        Each item in project_data_batch is a dict with 'summary', 'star_count', etc.
        The persona dictionary should contain 'name', 'title', 'description', and 'prompt' (template).
        """
        if not project_data_batch:
            return []

        categories_list_str = "\n".join(
            f"- \"{c['category']}\": {c['description']}" # Ensure category names are quoted for clarity in prompt
            for c in self.config_manager.get_categories()
        )

        persona_prompt_template = persona.get('prompt')
        if not persona_prompt_template:
            print(f"Error: Persona '{persona.get('name')}' is missing a prompt template.")
            return [ClassificationOutput(assigned_tag="Error", reason="Persona prompt missing")] * len(project_data_batch)

        individual_project_prompts = []
        for i, project_data in enumerate(project_data_batch):
            # Prepare metadata for formatting, handling None or NaN
            # Ensure star_count and fork_count are numbers, default to 0 if None/NaN
            star_count = project_data.get('star_count')
            fork_count = project_data.get('fork_count')
            
            formatted_star_count = int(star_count) if pd.notna(star_count) else 0
            formatted_fork_count = int(fork_count) if pd.notna(fork_count) else 0
            
            # Format dates, default to "N/A" if None/NaT
            created_at = project_data.get('created_at')
            updated_at = project_data.get('updated_at')

            formatted_created_at = str(created_at.date()) if pd.notna(created_at) and hasattr(created_at, 'date') else "N/A"
            formatted_updated_at = str(updated_at.date()) if pd.notna(updated_at) and hasattr(updated_at, 'date') else "N/A"
            
            # Ensure summary is a string
            summary_text = project_data.get('summary', "No summary provided.")
            if not isinstance(summary_text, str):
                summary_text = str(summary_text)

            # Ensure language is a string
            language_text = project_data.get('language', "Unknown")
            if not isinstance(language_text, str):
                language_text = str(language_text) if language_text is not None else "Unknown"

            # Get full README content
            readme_content = project_data.get('readme_md', '')
            if not isinstance(readme_content, str):
                readme_content = str(readme_content) if readme_content is not None else ''

            try:
                # The persona_prompt_template itself contains the persona's role description.
                # We just need to format it with the project-specific data.
                # The {categories} placeholder in the persona prompt will be filled by this categories_list_str.
                formatted_project_section = persona_prompt_template.format(
                    summary=summary_text,
                    readme_md=readme_content,
                    language=language_text,
                    star_count=formatted_star_count,
                    fork_count=formatted_fork_count,
                    created_at=formatted_created_at,
                    updated_at=formatted_updated_at,
                    categories=categories_list_str # Pass the formatted list of categories
                )
                individual_project_prompts.append(f"--- Project {i+1} ---\n{formatted_project_section}")
            except KeyError as e:
                print(f"KeyError during prompt formatting for persona {persona.get('name')}, project {project_data.get('repo_artifact_id', 'Unknown')}: {e}")
                # Add a placeholder error entry for this project
                individual_project_prompts.append(f"--- Project {i+1} ---\nError formatting prompt for this project. Cannot classify.")


        batch_project_details_str = "\n\n".join(individual_project_prompts)

        # Construct the overall batch prompt
        # The persona's title and description can frame the overall task.
        persona_title = persona.get('title', persona['name'])
        persona_description = persona.get('description', '')

        final_batch_prompt = f"""As {persona_title} ({persona_description}), your task is to review and classify the following {len(project_data_batch)} project(s).
For each project, use the specific instructions and context provided under its section.

{batch_project_details_str}

After reviewing all projects, please respond with a single JSON array. Each element in the array should be a JSON object corresponding to one project, in the exact order they were presented above. Each object must contain:
1. "assigned_tag": The category you assigned from the provided list.
2. "reason": A brief explanation for your choice, following the persona's specific instructions.

Example for two projects:
[
  {{ "assigned_tag": "Category A", "reason": "Reason for project 1..." }},
  {{ "assigned_tag": "Category B", "reason": "Reason for project 2..." }}
]
"""
        
        batch_output = self.execute_query(final_batch_prompt, BatchClassificationOutput)
        
        # Ensure the number of classifications matches the number of projects
        if len(batch_output.classifications) != len(project_data_batch):
            print(f"Warning: Mismatch in number of projects ({len(project_data_batch)}) and classifications ({len(batch_output.classifications)}) for persona {persona['name']}.")
            error_classification = ClassificationOutput(assigned_tag="Error", reason="Mismatch in batch processing output length")
            # Adjust the length of classifications to match project_data_batch
            final_classifications = batch_output.classifications[:len(project_data_batch)]
            while len(final_classifications) < len(project_data_batch):
                final_classifications.append(error_classification)
            batch_output.classifications = final_classifications
            
        return batch_output.classifications


if __name__ == '__main__':
    # Example Usage
    # Example Usage:
    # cfg_manager = ConfigManager() 
    # ai_service = AIService(config_manager=cfg_manager)
    # print("AIService initialized for standalone testing if needed.")
    pass
