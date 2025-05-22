# Dependency Graph v2

A tool for analyzing and visualizing dependencies across multiple repositories. This project helps you track and manage dependencies from various sources, map them to GitHub repositories, and generate comprehensive dependency snapshots.

## Features

- **Multiple Dependency Sources**: Fetch dependencies from different sources:
  - GitHub API (using GraphQL)
  - Package files analysis (using Gemini AI)
  - SPDX SBOM files (JSON and CSV formats)
- **Repository-specific Updates**: Update dependencies for specific repositories without affecting others
- **Dependency Snapshots**: Generate snapshots of dependencies across all repositories
- **Interactive Workflow**: Guided workflow for analyzing repositories
- **GitHub Repository Mapping**: Map dependencies to their source GitHub repositories using OSO's deps.dev package model

## Setup

1. Clone the repository
2. Install dependencies with Poetry:
   ```bash
   poetry install
   poetry env activate
   ```
3. Create a `.env` file with the following variables:
   ```
   OSO_API_KEY=your_oso_api_key
   GITHUB_TOKEN=your_github_token
   GEMINI_API_KEY=your_gemini_api_key
   ```

To get an OSO API key, go [here](https://docs.opensource.observer/docs/get-started/python).

## Usage

### Initialize Repository Sources

```bash
python -m src.scripts.initialize_repository_sources
```

### Analyze a Repository

```bash
python -m src.cli.main_cli dependencies analyze-repo https://github.com/username/repo
```

### Import SBOM Files

#### JSON Format

```bash
python -m src.cli.main_cli dependencies import-sbom path/to/sbom.json https://github.com/username/repo
```

#### CSV Format

```bash
python -m src.cli.main_cli dependencies import-csv path/to/sbom.csv https://github.com/username/repo
```

### Generate Dependency Snapshot

The dependency snapshot is automatically generated after analyzing a repository or importing an SBOM file. You can also generate it manually:

```bash
python -m src.cli.main_cli dependencies generate-snapshot
```

### Analyze Dependencies

```bash
python -m src.cli.main_cli dependencies analyze --repos https://github.com/username/repo --sources github_api package_files sbom
```

## Repository Sources

Repository sources are stored in `data/repository_sources.json`. Each repository can have multiple sources:

```json
[
  {
    "repo_url": "https://github.com/username/repo",
    "sources": [
      {
        "type": "github_api",
        "enabled": true,
        "priority": 1
      },
      {
        "type": "package_files",
        "enabled": true,
        "priority": 2,
        "files": [
          "https://github.com/username/repo/blob/master/package.json"
        ]
      },
      {
        "type": "sbom",
        "enabled": true,
        "priority": 3,
        "format": "json",
        "location": {
          "type": "local",
          "path": "data/sbom_exports/username_repo_123456.json"
        }
      }
    ],
    "last_updated": null
  }
]
```

## Output Files

- `output/dependencies.json`: Contains all dependencies for all repositories
- `output/dependency_snapshot.json`: Contains a snapshot of dependencies across all repositories
- `output/repo_status.txt`: Contains the status of each repository

## Architecture

The codebase is organized into several modules:

- `src/cli`: Command-line interface for dependency management
- `src/config`: Configuration and settings
- `src/pipeline`: Core pipeline components
- `src/processing`: Dependency source implementations
- `src/utils`: Utility functions
- `src/scripts`: Standalone scripts for various operations

## Dependency Sources

### GitHub API

Uses GitHub's GraphQL API to fetch dependencies from the dependency graph.

### Package Files

Analyzes package files (e.g., package.json, build.gradle) using Gemini AI to extract dependencies.

### SPDX SBOM

Imports dependencies from SPDX SBOM files in JSON or CSV format.

## Mapping Dependencies to GitHub Repositories

The project uses OSO's deps.dev package model to map dependencies to their source GitHub repositories. This mapping is performed by:

```bash
python -m src.scripts.map_dependencies_to_github
```

This creates a mapping cache in `data/package_github_mappings.csv` to speed up future lookups.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
