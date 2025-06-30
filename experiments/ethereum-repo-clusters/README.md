# Ethereum Repo Clusters

A Python module for categorizing Ethereum repositories using AI-based analysis.

## Overview

This project implements a pipeline to:
1.  Fetch repository data from the OSO (Open Source Observer) database.
2.  Retrieve corresponding README files from GitHub.
3.  Generate concise project summaries using Gemini AI.
4.  Employ multiple configurable AI personas to categorize each project based on its full README content, summary, and metadata.
5.  Consolidate categorizations and produce a final recommended category.

The entire process is managed via a Command Line Interface (CLI).

## Features

-   Quickly fetches comprehensive repository metadata via OSO.
-   Retrieves and processes README.md files from GitHub with robust error handling.
-   Utilizes Gemini AI for intelligent summary generation.
-   Supports an arbitrary number of configurable AI personas.
-   Provides detailed tracking of repository status (active/inactive, fork/non-fork).
-   Handles empty or error READMEs gracefully with "UNCATEGORIZED" status.
-   Test mode for quick runs on a subset of data.
-   Outputs data at various stages in Parquet and CSV formats.
-   Supports easy resumption of processing and addition of new repositories.
-   Features comprehensive progress bars at multiple levels for better visibility into processing status.
-   Automatically saves progress after each step, allowing for seamless recovery from interruptions and incremental processing.

## Prerequisites

-   Python 3.10+
-   Poetry (for dependency management)
-   Access to OSO, GitHub, and Gemini APIs.

## Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/ethereum/ethereum-repo-clusters.git
    cd ethereum-repo-clusters
    ```

2.  **Install Poetry (if not already installed):**
    ```bash
    curl -sSL https://install.python-poetry.org | python3 -
    ```

3.  **Install dependencies and activate the virtual environment:**
    ```bash
    poetry install
    poetry env activate
    ```
    This will:
    - Create a virtual environment automatically
    - Install all dependencies from `pyproject.toml`
    - Activate the virtual environment

4.  **Create a `.env` file** in the project root directory (`ethereum-repo-clusters/`) and add your API keys:
    ```env
    OSO_API_KEY="your_oso_api_key"
    GITHUB_TOKEN="your_github_personal_access_token"
    GEMINI_API_KEY="your_gemini_api_key"
    ```
    These keys are loaded via `ethereum-repo-clusters/config/settings.py`.

## Configuration

The project uses a combination of a JSON configuration file and Python modules for settings:

-   **`pipeline_config.json`**:
    -   Located at the project root.
    -   Controls operational settings like `output_dir`, `test_mode`, `test_mode_limit`, AI model name (`gemini_model`), and batch sizes for AI processing.
    -   If this file is missing, it will be automatically created with default values on the first run.
    -   Values in this file override defaults sourced from Python modules.

-   **AI Personas (`ethereum-repo-clusters/config/prompts/personas.py`):**
    -   Define the different AI personas used for categorization.
    -   Each persona is a dictionary with `name`, `title`, `description`, and a `prompt` template.
    -   Modify this Python list directly to add, remove, or change personas.

-   **Categories (`ethereum-repo-clusters/config/prompts/categories.py`):**
    -   Defines the list of possible categories projects can be assigned to.
    -   Includes `CATEGORIES` (list of dicts with `category` and `description`) and `CATEGORY_NAMES` (a simple list of category names).
    -   Edit this file to update the categorization taxonomy.

-   **Prompt Templates (`ethereum-repo-clusters/config/prompts/summary_prompts.py`):**
    -   Contains `SUMMARY_PROMPT` (for generating project summaries).
    -   These are used by the `AIService`.

-   **Core Settings (`ethereum-repo-clusters/config/settings.py`):**
    -   Loads API keys from the `.env` file.
    -   Defines default values for `GEMINI_MODEL` and `OUTPUT_DIR` if not specified in `pipeline_config.json`.

## Usage (CLI)

The project is operated via the command line. **Poetry is recommended** for managing the virtual environment and dependencies.

**General Command Structure:**
```bash
# With Poetry (recommended)
poetry run python -m ethereum-repo-clusters [GLOBAL_OPTIONS] COMMAND [COMMAND_OPTIONS]

# Or activate Poetry shell first, then run directly
poetry shell
python -m ethereum-repo-clusters [GLOBAL_OPTIONS] COMMAND [COMMAND_OPTIONS]
```

**Global Options:**
-   `--test-mode`: Runs the specified command(s) in test mode, processing a limited number of repositories (defined by `test_mode_limit` in `pipeline_config.json`, sorted by stars).

**Main Commands:**

-   **`fetch_repos`**: Fetches repository data from OSO and READMEs from GitHub.
    ```bash
    poetry run python -m ethereum-repo-clusters fetch_repos
    ```
    -   `--force-refresh`: Wipes existing raw repository data and re-fetches.
    -   `--fetch-new-only`: Only fetches repositories that don't exist in current data.

-   **`generate_summaries`**: Generates AI summaries for fetched repositories.
    ```bash
    poetry run python -m ethereum-repo-clusters generate_summaries
    ```
    -   `--force-refresh`: Wipes existing summaries and regenerates them.
    -   `--new-only`: Only generates summaries for repositories that don't have summaries yet.

-   **`categorize`**: Categorizes projects using all defined AI personas.
    ```bash
    poetry run python -m ethereum-repo-clusters categorize
    ```
    -   `--force-refresh`: Wipes existing categorizations and re-runs.
    -   `--persona <persona_name>`: Processes only the specified persona. Can be combined with `--force-refresh`. Example:
        ```bash
        poetry run python -m ethereum-repo-clusters categorize --persona technical_reviewer --force-refresh
        ```
    -   `--new-only`: Only categorizes repositories that don't have categories yet.

-   **`consolidate`**: Consolidates categorizations from all personas and generates final project recommendations.
    ```bash
    poetry run python -m ethereum-repo-clusters consolidate
    ```
    *(This step does not typically require a force-refresh as it always processes the latest categorized data.)*

-   **`run_all`**: Runs the complete pipeline from start to finish.
    ```bash
    poetry run python -m ethereum-repo-clusters run_all
    ```
    -   `--force-refresh-all`: Wipes all existing data and re-runs the entire pipeline.
    -   `--use-unified`: Uses the unified processor approach (recommended).

**Persona Management (Informational):**
The CLI includes commands related to personas, but due to refactoring, persona definitions are now managed directly in `ethereum-repo-clusters/config/prompts/personas.py`. These CLI commands are informational:

-   `poetry run python -m ethereum-repo-clusters personas list`: Lists personas currently defined in `personas.py`.
-   `poetry run python -m ethereum-repo-clusters personas add ...`: Provides instructions on how to add a persona by editing `personas.py`.
-   `poetry run python -m ethereum-repo-clusters personas remove <name>`: Provides instructions on how to remove a persona by editing `personas.py`.

**Example Full Run in Test Mode with Full Refresh:**
```bash
poetry run python -m ethereum-repo-clusters --test-mode run_all --force-refresh-all --use-unified
```

## Workflow

The unified processor combines all steps into a single efficient pipeline:

1.  **Process Repositories (`process_unified`):**
    -   Repository metadata is fetched from OSO, including fork status and activity tracking.
    -   README.md content is fetched from GitHub with robust error handling.
    -   For each repository with a valid README:
        -   A summary is generated immediately.
        -   All personas categorize the repository in sequence.
        -   Results are stored with timestamps for each operation.
    -   For repositories with empty or error READMEs:
        -   Status is tracked as "EMPTY" or "ERROR".
        -   All categorizations are marked as "UNCATEGORIZED".
    -   A final recommendation is determined based on the most common category across personas.
    -   Output: `output/ethereum_repos_unified.parquet` and `output/ethereum_repos_unified.csv`.

The unified processor offers several advantages:
-   Single pass through repositories (more efficient)
-   Better error handling and status tracking
-   Easier to resume processing or add new repositories
-   Comprehensive data structure with all information in one place
-   Timestamps for all operations for better traceability
-   Detailed progress bars for tracking processing status at multiple levels
-   CSV output with README text removed for improved readability
-   Checkpoint system that saves progress after each step
-   Incremental saving that preserves work even if interrupted
-   Automatic resume capability that continues from where it left off

## Output Files

All output data is stored in the directory specified by `output_dir` in `pipeline_config.json` (default is `output/`).

### Unified Processor Output

-   **`ethereum_repos_unified.parquet`**: Complete dataset with all repository metadata, README content, summaries, persona categorizations, and final recommendations.
-   **`ethereum_repos_unified.csv`**: CSV version of the unified dataset with README text removed for improved readability.

### Step-by-Step Pipeline Output (Alternative)

If using the step-by-step approach instead of the unified processor:

-   **`devtooling_raw.parquet`**: Raw data fetched from OSO, augmented with GitHub README content.
-   **`devtooling_summarized.parquet`**: Repositories with their AI-generated summaries.
-   **`categorized/<persona_name>.parquet`**: Dataframe for each persona, containing the original summary data plus that persona's assigned category and reason.
-   **`devtooling_full.parquet`**: The final consolidated dataset, with one row per project, including the overall recommendation, total stars, repo count, sample summary, and individual persona category modes.
-   **`devtooling_consolidated.csv`**: CSV version of the final consolidated dataset.