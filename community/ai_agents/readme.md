# AI Agents for Dependency Analysis - Training Data

## Project Overview
This experiment uses AI agents to analyze software dependency graphs and propose funding allocations for open source projects. Our goal is to create models that can:
- Distribute grant funding efficiently to critical infrastructure and upstream dependencies
- Align funding decisions with community preferences
- Validate proposals through expert review and pairwise comparisons

## Quick Start
1. Browse the sample data in the `./data` folder
2. Access OSO's complete datasets via [BigQuery](https://docs.opensource.observer/docs/integrate/)
3. Run our analysis using either:
   - Local Jupyter: `DataPrep.ipynb`
   - [Google Colab](https://colab.research.google.com/drive/1DpuX0A0ZVdFn63V2aKlJ8hQ2ZyPLwgp8?usp=sharing)
4. Experiment with model training using [Vertex AI](https://cloud.google.com/vertex-ai/docs/training/overview)

## Available Datasets

### Summary
- 2,010 Git repositories
- 12,305 Package dependencies
- 185,285 Git users

### Core Data Files
- `core_repos.csv`: Ethereum Core repository list with metadata
- `dep_repos.csv`: Direct dependencies tracked by OSO
- `repo_metrics.csv`: Repository statistics (stars, commits, etc.)
- `dep_graph.parquet`: First-level dependency relationships
- `events.parquet`: Detailed GitHub activity since 2017

### Activity Metrics Tracked
| Event Type | Count |
|------------|-------|
| Issue Comments | 371,754 |
| PR Review Comments | 331,840 |
| Code Commits | 302,096 |
| Repository Stars | 256,177 |
| PRs Opened | 149,180 |
| PRs Closed | 145,268 |
| PRs Merged | 123,502 |
| Repository Forks | 108,210 |
| Issues Opened | 81,699 |
| Issues Closed | 64,940 |
| Releases Published | 5,802 |
| PRs Reopened | 2,588 |
| Issues Reopened | 2,214 |

## Additional Resources
- Get more data (free): [OSO Documentation](https://docs.opensource.observer/docs/integrate/)
- Ask questions: [OSO Discord](https://www.opensource.observer/discord)
- Report issues: Open an issue in this repository
