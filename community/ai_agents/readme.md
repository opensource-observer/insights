# AI Agents for Dependency Analysis - Training Data

## Project Overview
This experiment uses AI agents to analyze software dependency graphs and propose funding allocations for open source projects. Our goal is to create models that can:
- Distribute grant funding efficiently to critical infrastructure and upstream dependencies
- Align funding decisions with community preferences
- Validate proposals through expert review and pairwise comparisons

## Quick Start
1. Explore the sample dependency data at `./data/unweighted_graph.csv` and `./data/test_weighted_graph.json`
2. Try running the `Example_WeightedGraph.ipynb` notebook to see how we might construct a weighted graph to make funding decisions

**Your objective is to create a better version of the weighted graph that we should deploy funding decisions on!**

## Next Steps
1. Ingest repository metrics (`./data/repo_metrics.csv`) and activity data (`./data/events.parquet`) for ideas on how to weight the graph
2. Check out OSO's complete datasets via [BigQuery](https://docs.opensource.observer/docs/integrate/)
3. Experiment with model training using [Vertex AI](https://cloud.google.com/vertex-ai/docs/training/overview)

## How It Works

The initial graph is created from package metadata and raw SBOM data from Ethereum and the top consensus and execution layer projects (according to https://clientdiversity.org). 

We map each package to a repository and create a dependency graph.

Currently, the dependency graph has three levels:
1. Ethereum (all repos except go-ethereum)
2. Ethereum clients (go-ethereum, nethermind, etc.) and direct dependencies of Ethereum repos
3. Dependencies of Ethereum clients

The dependency graph considers packages for Python, JavaScript, Go, and Rust.

We haven't implemented the next level of dependencies yet, but this first version gives us a graph of about 6,000 nodes (resolved from around 40,000 packages) and 30,000 edges.

The notebook used to create the initial graph is `DataPrep.ipynb`. Let us know if you find any issues with the data or the graph construction! Feel free to fork it and create your own graph!

## GitHub Activity

We've also included a parquet file with 1.5M rows of GitHub activity data from 2020 to 2024 for all relevant repositories.

This includes:

| Event Type | Count |
|------------|-------|
| Code Commits | 740,390 |
| Issue Comments | 1,078,645 |
| Repository Forks | 224,868 |
| Issues Opened | 296,934 |
| Issues Closed | 185,505 |
| Issues Reopened | 7,700 |
| PRs Opened | 423,758 |
| PRs Closed | 445,122 |
| PRs Merged | 364,273 |
| PRs Reopened | 4,476 |
| PR Review Comments | 681,945 |
| Releases Published | 19,600 |
| Stars | 542,384 |

Total Git Users: 328,414

## Additional Resources
- Get more data (free): [OSO Documentation](https://docs.opensource.observer/docs/integrate/)
- Ask questions: [OSO Discord](https://www.opensource.observer/discord)
- Report issues: Open an issue in this repository
