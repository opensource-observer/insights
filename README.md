# Insights  [![License: Apache 2.0][license-badge]][license]

[license]: https://opensource.org/license/apache-2-0/
[license-badge]: https://img.shields.io/badge/License-Apache2.0-blue.svg

This repository contains insights and exploratory data analysis on the health of open source software ecosystems. 

You can also find our folder of public Colab notebooks, [here](https://drive.google.com/drive/folders/1mzqrSToxPaWhsoGOR-UVldIsaX1gqP0F).

Notebooks are included so others can get inspiration and understand/improve upon our analysis. Where practical, copies of data used to generate insights has been saved in CSV or JSON format. However, many of the notebooks rely on direct queries to the data warehouse and therefore will not run locally without a live connection. Note: not all of these notebooks are actively maintained, so some queries may go stale over time.

## Getting Started

For most local queries, you'll want to connect directly to BigQuery and query OSO's versioned mart models (anything that ends in a v0 or v1).

Virtually every notebook begins with the following:

```
from google.cloud import bigquery
import pandas as pd
import os

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = # PATH TO YOUR CREDENTIALS JSON
GCP_PROJECT = # YOUR GCP PROJECT NAME

client = bigquery.Client(GCP_PROJECT)
```

Once you've connected, here are some sample queries. These examples pull from `oso_playground` (a small subset of all data) for testing purposes. Use `oso` for the full dataset (many terabytes).

Get all the GitHub repos by project:

```
results = client.query("""
    select
        project_name,
        artifact_namespace,
        artifact_name
    from `oso_playground.artifacts_by_project_v1`
    where artifact_source = 'GITHUB'
""")
df = results.to_dataframe()
```

Get a snapshot of all of OSO's static onchain metrics:

```
results = client.query("""
    select *
    from `oso_playground.onchain_metrics_by_project_v1`
""")
df = results.to_dataframe()
```

Get timeseries metrics for Uniswap:

```
results = client.query("""
    select
        m.metric_name,
        p.project_name,
        tsm.sample_date,
        tsm.amount
    from `oso_playground.timeseries_metrics_by_project_v0` as tsm
    join `oso_playground.metrics_v0` as m
        on tsm.metric_id = m.metric_id
    join `oso_playground.projects_v1` as p
        on tsm.project_id = p.project_id
    where p.project_name = 'uniswap'
    order by sample_date
""")
df = results.to_dataframe()
```

When you are ready to move to a larger dataset, remember to swap out `oso_playground` for `oso`.

## Repository Structure

Here's an overview of the repository structure:

```
analysis
└── dependencies
└── ecosystem_reports
└── XYZ chain ...

community
└──datasets
└──notebook_templates

experiments
└── bounties
└── retropgf3_simulation
└── etc...

scripts
visualizations
```

### Analysis

The analysis folder contains the bulk of the analysis and insights, mostly in the form of Jupyter Notebooks that leverage the OSO data warehouse and API. These are mainly provided for reference and to provide inspiration for others. They are not actively maintained and links will go stale over time. The dependencies folder contains scripts that are used to generate the dependency graph visualizations. The ecosystem_reports folder contains reports that are generated on a regular basis and published to the OSO blog.


### Community 

The community folder contains datasets and notebook templates that may be useful to new contributors. These provide sample queries and visualization tools, as well as steps for reproducing analysis that goes into the ecosystem reports. This is also the home for bounties we host.

### Experiments

The experiments folder contains experimental analysis and insights that are not yet ready for production. 

### Scripts

The scripts folder contains scripts for fetching data from the OSO API and data warehouse. It also includes some scripts for fetching GitHub or blockchain data on an ad hoc basis.

### Visualizations

The visualizations folder contains visualizations that are used in many of the reports, such as sankeys and heatmaps. Most of our visualizations are generated in Python using matplotlib, seaborn, and plotly.

# Contributing

We welcome contributions to this repository. Please see the [contributing guide](https://docs.opensource.observer/docs/contribute/) for more information about the types of contributions we're looking for. If you are an analyst or data scientist interested in becoming a regular contributor, please apply to join to the Kariba Data Collective [here](https://www.opensource.observer/data-collective).

In order to query large amounts of OSO data, you will need to subscribe to one or more of our public datasets on BigQuery. See here for [documentation](https://docs.opensource.observer/docs/integrate/) on how to do this.
