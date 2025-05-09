import sys
import os
import json
import argparse
from pathlib import Path
import nbformat
from pydantic import BaseModel, Field
from typing import List, Optional
from google import genai
from dotenv import load_dotenv

"""
generate_rule_from_tutorial.py

Auto-generates a Cursor .mdc rule file from a given tutorial notebook or markdown
by extracting structured workflow steps via Gemini.
"""

# llm setup
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY)
MODEL = 'gemini-2.0-flash'

# structured outputs
class Step(BaseModel):
    title: str = Field(..., description="High-level step title")
    description: Optional[str] = Field(
        None,
        description="Brief explanation of the step or None if not provided"
    )

class TutorialRule(BaseModel):
    steps: List[Step] = Field(
        ..., description="Ordered list of steps for the tutorial rule"
    )


# helpers
def ensure_rules_dir() -> Path:
    """Ensure .cursor/rules exists and return the path."""
    rules_dir = Path(".cursor/rules")
    rules_dir.mkdir(parents=True, exist_ok=True)
    return rules_dir


# tutorial parsers
def parse_markdown_file(path: Path) -> str:
    """Return raw markdown text from a .md tutorial."""
    return path.read_text(encoding="utf-8")


def parse_notebook_file(path: Path) -> str:
    """Concatenate markdown + code cells from a .ipynb tutorial."""
    nb = nbformat.read(str(path), as_version=4)
    texts: list[str] = []
    for cell in nb.cells:
        if cell.cell_type in ("markdown", "code"):
            texts.append(cell.source)
    return "\n\n".join(texts)


# llm prompt & call
TEMPLATE_PROMPT = """
    You are an AI assistant whose sole job is to extract the high-level workflow steps from a single data-science tutorial.  
    Your task is to identify the main steps in the tutorial and provide a structured JSON output.
    The goal is for a user with no prior knowledge of the tutorial to follow your output and reproduce similar results.

    - Do **not** include any code snippets.  
    - If a step relies on a crucial function, class, or module, simply mention its name (e.g., `load_data()` or `LinearRegression()`) and include it in the step.  
    - Focus exclusively on what the user needs to do at each stage, and focus more on summarization.  
    - Ignore images, tables, comments, and implementation details.

    Return **only valid JSON** matching this schema:
    ```json
        {{  
        "steps": [  
           {{  
            "title": "<Step title>",  
            "description": "<Brief explanation or null>" 
            }}
        ]  
        }}
    ```

    Tutorial content (delimited by triple backticks):
    ```
    {tutorial_content}
    ```
"""


def call_llm(client: genai.client, structured_output: object, model: str, prompt: str) -> dict:
    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config={
            "response_mime_type": "application/json",
            "response_schema": structured_output,
        },
    )
    return response.parsed
    

# mdc file creator
GENERIC_NOTE = (
        "\n---\n\n"
        "**How to use this rule**\n\n"
        "This tutorial is intended as a *manual* workflow. Replace all `{placeholders}` with your own values.\n"
        "If a step is not applicable to your problem, you may skip it—just make sure to tell the user *which* step you are omitting and **why**.\n"
    )

def render_mdc(slug: str, tutorial_rel_path: str, rule: TutorialRule) -> str:
    """Render the final MDC text from a TutorialRule object."""
    front_matter = (
        "---\n"
        f"description: Walk through the {slug.replace('-', ' ')} tutorial with your own data\n"
        "globs:\n"
        f"  - \"{tutorial_rel_path}\"\n"
        "alwaysApply: false\n"
        "---\n\n"
    )

    body_lines: list[str] = []
    for idx, step in enumerate(rule.steps, 1):
        body_lines.append(f"{idx}. **{step.title}**")
        if step.description:
            body_lines.append(f"   - {step.description}")
        body_lines.append("")

    body = "\n".join(body_lines).rstrip()

    return front_matter + body + GENERIC_NOTE


# main
def main():
    parser = argparse.ArgumentParser(description="Generate Cursor tutorial rule files.")
    parser.add_argument(
        "--paths", nargs='+', required=True,
        help="List of tutorial file paths"
    )

    parser.add_argument(
        "--slugs", nargs='+', required=True,
        help="List of corresponding tutorial slugs"
    )

    args = parser.parse_args()

    tutorial_paths = args.paths
    slugs = args.slugs
    if len(tutorial_paths) != len(slugs):
        print("Error: The number of paths and slugs must match.")
        sys.exit(1)

    rules_dir = ensure_rules_dir()

    for tutorial, slug in zip(tutorial_paths, slugs):
        path = Path(tutorial)
        if not path.exists():
            print(f"File not found: {tutorial}")
            continue

        if path.suffix == ".ipynb":
            content = parse_notebook_file(path)
        elif path.suffix == ".md":
            content = parse_markdown_file(path)
        else:
            print(f"Unsupported file type: {tutorial}")
            continue

        prompt = TEMPLATE_PROMPT.format(tutorial_content=content)

        try:
            steps_json = call_llm(client, TutorialRule, MODEL, prompt)
        except Exception as exc:
            print(f"LLM call failed for {tutorial}: {exc}")
            continue

        mdc_text = render_mdc(slug, path.as_posix(), steps_json)
        out_path = rules_dir / f"tutorial-{slug}.mdc"
        out_path.write_text(mdc_text, encoding="utf-8")
        print(f"Generated rule: {out_path}")

if __name__ == "__main__":
    main()
