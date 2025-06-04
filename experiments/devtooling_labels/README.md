# DevTooling Labels

A Python package for automatically categorizing development tools and libraries based on their README content using AI-driven analysis and multiple personas.

## Overview

This project implements a pipeline to:
1.  Fetch repository data from the OSO (Open Source Observer) database.
2.  Retrieve corresponding README files from GitHub.
3.  Generate concise project summaries using Google's Gemini AI.
4.  Employ multiple configurable AI personas to categorize each project based on its summary and metadata.
5.  Consolidate these categorizations, using a star-count weighted approach for projects with multiple repositories, to produce a final recommended category.

The entire process is managed via a Command Line Interface (CLI).

## Features

-   Fetches comprehensive repository data via OSO.
-   Retrieves and processes README.md files from GitHub.
-   Utilizes Google's Gemini AI for intelligent summary generation.
-   Employs a multi-persona approach for nuanced project categorization.
-   Supports an arbitrary number of configurable AI personas.
-   Calculates final project recommendations using star-count weighted consolidation for multi-repository projects.
-   Modular pipeline allowing individual step execution and data refresh.
-   Test mode for quick runs on a subset of data.
-   Outputs data at various stages in Parquet and CSV formats.

## Prerequisites

-   Python 3.10+
-   Access to OSO, GitHub, and Google Gemini APIs.

## Installation

1.  **Clone the repository:**
    ```bash
    git clone <your-repository-url>
    cd devtooling_labels
    ```

2.  **Set up a virtual environment (recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Install the package in editable mode (optional, for development):**
    ```bash
    pip install -e .
    ```

5.  **Create a `.env` file** in the project root directory (`devtooling_labels/`) and add your API keys:
    ```env
    OSO_API_KEY="your_oso_api_key"
    GITHUB_TOKEN="your_github_token" # A GitHub Personal Access Token with repo access
    GEMINI_API_KEY="your_gemini_api_key"
    ```
    These keys are loaded via `devtooling_labels/config/settings.py`.

## Configuration

The project uses a combination of a JSON configuration file and Python modules for settings:

-   **`pipeline_config.json`**:
    -   Located at the project root.
    -   Controls operational settings like `output_dir`, `test_mode`, `test_mode_limit`, AI model name (`gemini_model`), and batch sizes for AI processing.
    -   If this file is missing, it will be automatically created with default values on the first run.
    -   Values in this file override defaults sourced from Python modules.

-   **AI Personas (`devtooling_labels/config/prompts/personas.py`):**
    -   Define the different AI personas used for categorization.
    -   Each persona is a dictionary with `name`, `title`, `description`, and a `prompt` template.
    -   Modify this Python list directly to add, remove, or change personas.

-   **Categories (`devtooling_labels/config/prompts/categories.py`):**
    -   Defines the list of possible categories projects can be assigned to.
    -   Includes `CATEGORIES` (list of dicts with `category` and `description`) and `CATEGORY_NAMES` (a simple list of category names).
    -   Edit this file to update the categorization taxonomy.

-   **Prompt Templates (`devtooling_labels/config/prompts/summary_prompts.py`):**
    -   Contains `SUMMARY_PROMPT` (for generating project summaries) and `TAGS_PROMPT` (for an auxiliary tag generation, currently not central to categorization).
    -   These are used by the `AIService`.

-   **Core Settings (`devtooling_labels/config/settings.py`):**
    -   Loads API keys from the `.env` file.
    -   Defines default values for `GEMINI_MODEL` and `OUTPUT_DIR` if not specified in `pipeline_config.json`.

## Usage (CLI)

The project is operated via the command line using `python -m devtooling_labels`.

**General Command Structure:**
```bash
python -m devtooling_labels [GLOBAL_OPTIONS] COMMAND [COMMAND_OPTIONS]
```

**Global Options:**
-   `--test-mode`: Runs the specified command(s) in test mode, processing a limited number of repositories (defined by `test_mode_limit` in `pipeline_config.json`, sorted by stars).

**Main Commands:**

-   **`fetch_repos`**: Fetches repository data from OSO and READMEs from GitHub.
    ```bash
    python -m devtooling_labels fetch_repos
    ```
    -   `--force-refresh`: Wipes existing raw repository data and re-fetches.
    -   `--fetch-new-only`: Only fetches repositories that don't exist in current data.

-   **`generate_summaries`**: Generates AI summaries for fetched repositories.
    ```bash
    python -m devtooling_labels generate_summaries
    ```
    -   `--force-refresh`: Wipes existing summaries and regenerates them.
    -   `--new-only`: Only generates summaries for repositories that don't have summaries yet.

-   **`categorize`**: Categorizes projects using all defined AI personas.
    ```bash
    python -m devtooling_labels categorize
    ```
    -   `--force-refresh`: Wipes existing categorizations and re-runs.
    -   `--persona <persona_name>`: Processes only the specified persona. Can be combined with `--force-refresh`. Example:
        ```bash
        python -m devtooling_labels categorize --persona keyword_spotter --force-refresh
        ```
    -   `--new-only`: Only categorizes repositories that don't have categories yet.

-   **`consolidate`**: Consolidates categorizations from all personas and generates final project recommendations.
    ```bash
    python -m devtooling_labels consolidate
    ```
    *(This step does not typically require a force-refresh as it always processes the latest categorized data.)*

**Persona Management (Informational):**
The CLI includes commands related to personas, but due to refactoring, persona definitions are now managed directly in `devtooling_labels/config/prompts/personas.py`. These CLI commands are informational:

-   `python -m devtooling_labels personas list`: Lists personas currently defined in `personas.py`.
-   `python -m devtooling_labels personas add ...`: Provides instructions on how to add a persona by editing `personas.py`.
-   `python -m devtooling_labels personas remove <name>`: Provides instructions on how to remove a persona by editing `personas.py`.

**Example Full Run in Test Mode with Full Refresh:**
```bash
python -m devtooling_labels --test-mode run_all --force-refresh-all
```

## Workflow

1.  **Fetch Data (`fetch_repos`):**
    -   Repository metadata is fetched from OSO.
    -   README.md content is fetched from GitHub for these repositories.
    -   Output: `output/raw_repos_data.parquet`

2.  **Generate Summaries (`generate_summaries`):**
    -   READMEs are processed by Gemini AI to create concise summaries.
    -   Output: `output/summaries_data.parquet`

3.  **Categorize by Persona (`categorize`):**
    -   Each project summary (with metadata) is evaluated by every defined AI persona.
    -   Each persona assigns a category based on its specific prompt and the global category list.
    -   Output: Individual Parquet files per persona in `output/categorized/` (e.g., `output/categorized/keyword_spotter_categorized.parquet`).

4.  **Consolidate Recommendations (`consolidate`):**
    -   Categorizations from all personas are merged.
    -   For each project:
        -   If it's a single-repository project, the recommendation is based on a star-weighted aggregation of persona assignments for that repo.
        -   If it's a multi-repository project, the recommendation is determined by a star-count weighted aggregation of all persona assignments across all its repositories. The category with the highest total star weight wins.
    -   Output: `output/consolidated_data.parquet` and `output/consolidated_data.csv`.

## Output Files

All output data is stored in the directory specified by `output_dir` in `pipeline_config.json` (default is `output/`).

-   **`raw_repos_data.parquet`**: Raw data fetched from OSO, augmented with GitHub README content.
-   **`summaries_data.parquet`**: Repositories with their AI-generated summaries.
-   **`categorized/<persona_name>_categorized.parquet`**: Dataframe for each persona, containing the original summary data plus that persona's assigned category and reason.
-   **`consolidated_data.parquet`**: The final consolidated dataset, with one row per project, including the overall recommendation, total stars, repo count, sample summary, and individual persona category modes.
-   **`consolidated_data.csv`**: A CSV version of the final consolidated data for easier viewing.

## Development Notes
- The project uses `tqdm` for progress bars during long operations.
- `DataManager` class in `devtooling_labels/pipeline/data_manager.py` handles all data persistence (reading/writing Parquet files).
- `AIService` in `devtooling_labels/processing/ai_service.py` abstracts interactions with the Gemini API.
