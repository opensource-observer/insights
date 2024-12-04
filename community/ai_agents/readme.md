# AI Agents for Dependency Analysis - Training Data

This experiment explores using AI agents to analyze software dependency graphs and propose funding allocations that align with human values and preferences. The goal is to develop models that can efficiently and fairly distribute grant funding to critical open source dependencies while maintaining alignment with community preferences.

This repo includes some initial training data for the AI agents. You can get much more (for free) [here](https://docs.opensource.observer/docs/integrate/). We've also created a [Colab notebook](https://colab.research.google.com/drive/1DpuX0A0ZVdFn63V2aKlJ8hQ2ZyPLwgp8?usp=sharing) to help you get started.

## Overview

The goal of this experiment is to:
- Train AI models on dependency and contribution data
- Have models propose funding splits from a pool of funds
- Validate proposals against human preferences through:
  - Expert spot-checks
  - Pairwise comparisons
- Use the winning model(s) as an allocation mechanism

## Data Preparation

The `DataPrep.ipynb` notebook collects and processes OSO data about Ethereum Core repositories and their dependencies. It generates several datasets you can use to get started with your models:

### Core Repository Data
- `core_repos.csv`: List of all Ethereum Core repositories, including metadata like organization and repository names
- `dep_repos.csv`: List of all direct dependencies of Core repositories that are tracked by OSO

### Repository Metrics  
- `repo_metrics.csv`: Key metrics for all repositories including:
  - Stars, forks, and watchers
  - Contributor and commit counts
  - Creation and last update dates
  - Primary language and license

### Dependency Graph
- `dep_graph.parquet`: First-level dependency relationships showing:
  - Source repository (Core)
  - Dependency name and package manager
  - Mapped OSO project (if available)

### Activity Data
- `events.parquet`: GitHub activity data since 2017 including:
  - Commit counts
  - Pull requests
  - Issues
  - Comments
  - Code reviews
  - Stars and forks
  - Other interactions

## Getting Started

1. Explore the data in the `./data` folder and get familiar with the OSO schema
2. Ensure you have BigQuery access to OSO's datasets (see [documentation](https://docs.opensource.observer/docs/integrate/))
3. Run `DataPrep.ipynb` locally or fork the [Colab notebook](https://colab.research.google.com/drive/1DpuX0A0ZVdFn63V2aKlJ8hQ2ZyPLwgp8?usp=sharing)
4. Check out [Vertex AI](https://cloud.google.com/vertex-ai/docs/training/overview) for some ideas on how to train your models

## Contributing

For questions or suggestions, come say hi in the [OSO Discord](https://www.opensource.observer/discord) or open an issue in this repo.
