# SUNNY Metrics 🌞

## Background

The [SUNNY Awards](https://www.thesunnyawards.fun/) celebrate builders across the Superchain by awarding prizes based on project impact, contributions, and performance metrics. More than 540K OP in prizes will be awarded across 20 categories.

Open Source Observer is collaborating with partners such as Base, Charmverse, Farcaster, Forbes Web3, Gitcoin, and others to support this initiative by providing comprehensive data analytics.

## Objectives

Our primary goal is to derive and provide key metrics for each application that help reviewers evaluate them based on:

- Performance indicators
- Wallet activity
- Contract deployments
- NFT interactions
- Other relevant onchain data

## Getting Started

### Prerequisites

- **Python >= 3.8+**
- **pip** (for Python package management) or whatever you prefer

### Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/opensource-observer/insights
   cd community/sunnys-metrics
   ```

2. Install the required dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file in the root directory and add your credentials. You can use the provided `.env.example` as a template:

   ```bash
   cp .env.example .env
   ```

4. Add your API keys and configuration details in the `.env` file.

   **Example `.env` Configuration**

   ```
   ## Application data (from Gitcoin team)
   EZRF_API_KEY=

   ## Data sources (add here)
   FLIPSIDE_API_KEY=
   ```

## Project Structure

The project is organized into several modules, each containing specific queries:

- `queries/`: Directory containing query modules
  - `bridge.py`: Queries related to bridge metrics
  - `dex.py`: Queries for decentralized exchange metrics
  - `farcaster.py`: Queries for Farcaster-related metrics
  - `lending.py`: Queries for lending protocol metrics
  - `marketplace.py`: Queries for NFT marketplace metrics
  - `nft.py`: Queries for NFT-related metrics
  - `rwa.py`: Queries for Real World Asset metrics
  - `staking.py`: Queries for staking metrics
- `utils.py`: Utility functions for initializing the Flipside client and executing queries
- `config.py`: Configuration variables and constants

- `process_applications.ipynb`: Jupyter notebook for fetching and processing the application data
- `generate_metrics.ipynb`: Jupyter notebook for generating metrics for all projects

Each query module contains functions that return SQL queries for specific metrics. These functions are designed to be flexible and accept parameters like blockchain and contract address.

## Running the Notebooks

First, we process and normalize the application data in a Jupyter notebook. Then we apply queries to the data to generate metrics.

### Processing the Application Data

1. Launch Jupyter Notebook:

   ```bash
   jupyter notebook
   ```

2. Open the `process_applications.ipynb` file and run the cells to process the data.

   The raw data is saved to `data/applications.json` and a normalized version is saved to `data/applications_reviewed.csv`.

3. If you don't have an API key from Gitcoin, then you can just use the `applications_reviewed.csv` file as input for the metrics generation notebook.

### Generating Metrics

1. Launch Jupyter Notebook:

   ```bash
   jupyter notebook
   ```

2. Open the `generate_metrics.ipynb` file and run the cells to generate the metrics.

   The `generate_metrics.ipynb` notebook is the main entry point for generating metrics for all projects. It does the following:

   1. Loads the necessary modules and initializes the Flipside client.
   2. Reads the project data from a CSV file.
   3. Defines a mapping between project categories and their corresponding query modules.
   4. Implements a `query_project_metrics` function that:
      - Determines the appropriate query module based on the project category.
      - Executes all relevant queries for the project.
      - Logs the results, including execution time and status.
   5. Allows for batch processing of all projects or individual project testing.

## Contributing

We welcome contributions! Here's how you can help:

1. Fork the repository.
2. Create a new branch (`git checkout -b feature/my-feature`).
3. Make your changes and commit them (`git commit -am 'Add my feature'`).
4. Push to the branch (`git push origin feature/my-feature`).
5. Open a pull request.

## Contact

If you have any questions, feel free to reach out to Carl over Discord (cerv1) or open an issue in this repository and tag @ccerv1.
