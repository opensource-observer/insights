# Ethereum Repo Clusters

A Python package for automatically clustering Ethereum development tools and libraries based on their README content using AI-driven analysis and multiple personas.

## Overview

This project implements a pipeline to:
1.  Fetch repository data from the OSO (Open Source Observer) database.
2.  Retrieve corresponding README files from GitHub.
3.  Generate concise project summaries using Google's Gemini AI.
4.  Employ multiple configurable AI personas to categorize each project based on its summary and metadata.
5.  Consolidate these categorizations, using a star-count weighted approach for projects with multiple repositories, to produce a final recommended category.

The entire process is managed via a Command Line Interface (CLI).

## Features

-   Fetches comprehensive repository data via OSO, including fork status and activity tracking.
-   Retrieves and processes README.md files from GitHub with robust error handling.
-   Utilizes Google's Gemini AI for intelligent summary generation.
-   Employs a multi-persona approach for nuanced project categorization.
-   Supports an arbitrary number of configurable AI personas.
-   Calculates final project recommendations using star-count weighted consolidation.
-   Offers both modular pipeline and unified processing approaches.
-   Provides detailed tracking of repository status (active/inactive, fork/non-fork).
-   Handles empty or error READMEs gracefully with "UNCATEGORIZED" status.
-   Includes timestamps for all categorization operations.
-   Test mode for quick runs on a subset of data.
-   Outputs data at various stages in Parquet and CSV formats (with README text removed from CSV for readability).
-   Supports easy resumption of processing and addition of new repositories.
-   Features comprehensive progress bars at multiple levels for better visibility into processing status.

## Prerequisites

-   Python 3.10+
-   Access to OSO, GitHub, and Google Gemini APIs.

## Installation

1.  **Clone the repository:**
    ```bash
    git clone <your-repository-url>
    cd ethereum-repo-clusters
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

5.  **Create a `.env` file** in the project root directory (`ethereum-repo-clusters/`) and add your API keys:
    ```env
    OSO_API_KEY="your_oso_api_key"
    GITHUB_TOKEN="your_github_token" # A GitHub Personal Access Token with repo access
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
    -   Contains `SUMMARY_PROMPT` (for generating project summaries) and `TAGS_PROMPT` (for an auxiliary tag generation, currently not central to categorization).
    -   These are used by the `AIService`.

-   **Core Settings (`ethereum-repo-clusters/config/settings.py`):**
    -   Loads API keys from the `.env` file.
    -   Defines default values for `GEMINI_MODEL` and `OUTPUT_DIR` if not specified in `pipeline_config.json`.

## Usage (CLI)

The project is operated via the command line using `python -m ethereum-repo-clusters`.

**General Command Structure:**
```bash
python -m ethereum-repo-clusters [GLOBAL_OPTIONS] COMMAND [COMMAND_OPTIONS]
```

**Global Options:**
-   `--test-mode`: Runs the specified command(s) in test mode, processing a limited number of repositories (defined by `test_mode_limit` in `pipeline_config.json`, sorted by stars).

**Main Commands:**

-   **`fetch_repos`**: Fetches repository data from OSO and READMEs from GitHub.
    ```bash
    python -m ethereum-repo-clusters fetch_repos
    ```
    -   `--force-refresh`: Wipes existing raw repository data and re-fetches.
    -   `--fetch-new-only`: Only fetches repositories that don't exist in current data.

-   **`generate_summaries`**: Generates AI summaries for fetched repositories.
    ```bash
    python -m ethereum-repo-clusters generate_summaries
    ```
    -   `--force-refresh`: Wipes existing summaries and regenerates them.
    -   `--new-only`: Only generates summaries for repositories that don't have summaries yet.

-   **`categorize`**: Categorizes projects using all defined AI personas.
    ```bash
    python -m ethereum-repo-clusters categorize
    ```
    -   `--force-refresh`: Wipes existing categorizations and re-runs.
    -   `--persona <persona_name>`: Processes only the specified persona. Can be combined with `--force-refresh`. Example:
        ```bash
        python -m ethereum-repo-clusters categorize --persona keyword_spotter --force-refresh
        ```
    -   `--new-only`: Only categorizes repositories that don't have categories yet.

-   **`consolidate`**: Consolidates categorizations from all personas and generates final project recommendations.
    ```bash
    python -m ethereum-repo-clusters consolidate
    ```
    *(This step does not typically require a force-refresh as it always processes the latest categorized data.)*

**Persona Management (Informational):**
The CLI includes commands related to personas, but due to refactoring, persona definitions are now managed directly in `ethereum-repo-clusters/config/prompts/personas.py`. These CLI commands are informational:

-   `python -m ethereum-repo-clusters personas list`: Lists personas currently defined in `personas.py`.
-   `python -m ethereum-repo-clusters personas add ...`: Provides instructions on how to add a persona by editing `personas.py`.
-   `python -m ethereum-repo-clusters personas remove <name>`: Provides instructions on how to remove a persona by editing `personas.py`.

**Example Full Run in Test Mode with Full Refresh:**
```bash
# Legacy pipeline approach
python -m ethereum-repo-clusters --test-mode run_all --force-refresh-all

# New unified processor approach (recommended)
python -m ethereum-repo-clusters --test-mode run_all --force-refresh-all --use-unified
```

## Workflow

### Legacy Pipeline (Step-by-Step)

1.  **Fetch Data (`fetch_repos`):**
    -   Repository metadata is fetched from OSO.
    -   README.md content is fetched from GitHub for these repositories.
    -   Output: `output/devtooling_raw.parquet`

2.  **Generate Summaries (`generate_summaries`):**
    -   READMEs are processed by Gemini AI to create concise summaries.
    -   Output: `output/devtooling_summarized.parquet`

3.  **Categorize by Persona (`categorize`):**
    -   Each project summary (with metadata) is evaluated by every defined AI persona.
    -   Each persona assigns a category based on its specific prompt and the global category list.
    -   Output: Individual Parquet files per persona in `output/categorized/` (e.g., `output/categorized/keyword_spotter.parquet`).

4.  **Consolidate Recommendations (`consolidate`):**
    -   Categorizations from all personas are merged.
    -   For each project:
        -   If it's a single-repository project, the recommendation is based on a star-weighted aggregation of persona assignments for that repo.
        -   If it's a multi-repository project, the recommendation is determined by a star-count weighted aggregation of all persona assignments across all its repositories. The category with the highest total star weight wins.
    -   Output: `output/devtooling_full.parquet` and `output/devtooling_consolidated.csv`.

### New Unified Processor (Recommended)

The new unified processor combines all steps into a single efficient pipeline:

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

## Output Files

All output data is stored in the directory specified by `output_dir` in `pipeline_config.json` (default is `output/`).

### Legacy Pipeline Output

-   **`devtooling_raw.parquet`**: Raw data fetched from OSO, augmented with GitHub README content.
-   **`devtooling_summarized.parquet`**: Repositories with their AI-generated summaries.
-   **`categorized/<persona_name>.parquet`**: Dataframe for each persona, containing the original summary data plus that persona's assigned category and reason.
-   **`devtooling_full.parquet`**: The final consolidated dataset, with one row per project, including the overall recommendation, total stars, repo count, sample summary, and individual persona category modes.
-   **`devtooling_consolidated.csv`**: A CSV version of the final consolidated data for easier viewing.

### Unified Processor Output

-   **`ethereum_repos_unified.parquet`**: Comprehensive dataset containing all repositories with their metadata, summaries, and categorizations in a single structure.
-   **`ethereum_repos_unified.csv`**: A CSV version of the unified data for easier viewing, with README text removed and long text fields truncated for readability.

### Unified Data Structure

The unified processor creates a comprehensive data structure with the following key fields:

```json
{
  "repo_artifact_id": "...",
  "project_id": "...",
  "repo_artifact_namespace": "...",
  "repo_artifact_name": "...",
  "is_fork": true/false,
  "is_actively_maintained": true/false,
  "last_updated": "2024-12-01",
  "star_count": 100,
  "readme_status": "SUCCESS/EMPTY/ERROR",
  "summary": "...",
  "categorizations": [
    {
      "persona_name": "keyword_spotter",
      "category": "Developer Tools",
      "reason": "Contains keywords like 'CLI', 'build tool'...",
      "timestamp": "2025-01-05T09:15:00Z"
    },
    {
      "persona_name": "senior_strategist",
      "category": "Infrastructure",
      "reason": "Mature project with strong adoption...",
      "timestamp": "2025-01-05T09:15:01Z"
    },
    {
      "persona_name": "workflow_wizard",
      "category": "Developer Tools",
      "reason": "Streamlines development workflow...",
      "timestamp": "2025-01-05T09:15:02Z"
    }
  ],
  "final_recommendation": "Developer Tools",
  "processing_timestamp": "2025-01-05T09:15:02Z"
}
```

This structure makes it easy to:
- Track which repositories have been processed
- Identify repositories with errors or empty READMEs
- See the categorization from each persona with timestamps
- Filter repositories by fork status or activity
- Resume processing from where you left off

## Development Notes
- The project uses `tqdm` for progress bars during long operations, with detailed progress tracking at multiple levels:
  - Overall batch processing
  - Repository processing within each batch
  - README fetching for each repository
  - Categorization with each persona
- `DataManager` class in `ethereum-repo-clusters/pipeline/data_manager.py` handles all data persistence (reading/writing Parquet files).
- `AIService` in `ethereum-repo-clusters/processing/ai_service.py` abstracts interactions with the Gemini API.
- `UnifiedProcessor` in `ethereum-repo-clusters/pipeline/unified_processor.py` provides the new streamlined processing approach.
- The CLI in `ethereum-repo-clusters/cli/main_cli.py` supports both legacy and unified processing approaches.
- Output files are saved to the local `output/` directory in the current repository.

## New CLI Commands

### Unified Processing

```bash
# Process repositories with the unified processor
python -m ethereum-repo-clusters process_unified [OPTIONS]

# Options:
#   --force-refresh      Force refresh all data, ignoring existing.
#   --include-forks      Include forked repositories in processing.
#   --include-inactive   Include repositories not updated in the last year.
#   --limit INTEGER      Limit the number of repositories to process.
```

### Run All with Unified Processor

```bash
# Run the entire pipeline using the unified processor
python -m ethereum-repo-clusters run_all --use-unified [OPTIONS]

# Additional options with --use-unified:
#   --include-forks      Include forked repositories in processing.
#   --include-inactive   Include repositories not updated in the last year.
```

## Adding New Repositories

To add new repositories to the analysis:

1. The unified processor automatically detects which repositories have already been processed.
2. New repositories from OSO will be processed automatically on the next run.
3. To add repositories manually, you can:
   - Update the OSO query in `fetcher.py` to include additional repositories.
   - Create a custom script that adds repositories to the unified data structure.

## Error Handling

The unified processor handles errors gracefully:

- Empty READMEs: Marked with `readme_status="EMPTY"` and categorized as "UNCATEGORIZED".
- Error fetching README: Marked with `readme_status="ERROR"` and categorized as "UNCATEGORIZED".
- API errors during categorization: The specific persona's categorization is marked as "UNCATEGORIZED" with the error reason.

This approach ensures that all repositories are included in the final output, even if they couldn't be fully processed.
