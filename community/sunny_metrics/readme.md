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

### Example `.env` Configuration

```bash
# API Key for accessing Gitcoin data
EZRF_API_KEY=your_api_key_here

# Add other data sources here, e.g.:
# DUNE_API_KEY=your_dune_api_key
```

### Running the Notebook

We process and normalize the application data in a Jupyter notebook. To run the notebook:

1. Launch Jupyter Notebook:

   ```bash
   jupyter notebook
   ```

2. Open the `process_applications.ipynb` file and run the cells to process the data.

## Application Data Processing

We process each application submission using the following schema:

```python
def process_application(app):
    # Logic to extract and normalize data
    ...
```

The processed data includes:
- **Profile Information**: Name, bio, website, and more.
- **Contract Information**: Contracts deployed by the applicant and their wallet addresses.
- **Sunny Awards Metadata**: Project type, category, images, and more.

### Sample Output Format

The final output for each application will look like:

```json
{
  "id": "app_id",
  "attester": "attester_id",
  "recipient": "recipient_id",
  "name": "project_name",
  "profile_name": "applicant_name",
  "sunnyAwards_project_type": "project_type",
  ...
}
```

## Contributing

We welcome contributions! Here's how you can help:

1. Fork the repository.
2. Create a new branch (`git checkout -b feature/my-feature`).
3. Make your changes and commit them (`git commit -am 'Add my feature'`).
4. Push to the branch (`git push origin feature/my-feature`).
5. Open a pull request.


## Contact

If you have any questions, feel free to reach out to Carl over Discord (cerv1) or open an issue in this repository and tag @ccerv1.
