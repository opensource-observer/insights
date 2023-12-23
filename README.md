# Insights  [![License: Apache 2.0][license-badge]][license]

[license]: https://opensource.org/license/apache-2-0/
[license-badge]: https://img.shields.io/badge/License-Apache2.0-blue.svg

This repository contains insights and exploratory data analysis on the health of open source software ecosystems. 

Juypter Notebooks are included so others can get inspiration and understand/improve upon our analysis. Where practical, copies of data used to generate insights has been saved in CSV or JSON format. However, many of the notebooks rely on direct queries to the data warehouse and therefore will not run locally without API access. These notebooks are not actively maintained and links will go stale over time.

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

We welcome contributions to this repository. Please see the [contributing guide](https://docs.opensource.observer/docs/category/data-science) for more information about the types of contributions we're looking for. If you are an analyst or data scientist interested in becoming a regular contributor, please apply to join to the Kariba Data Collective [here](https://www.opensource.observer/data-collective).

In order to use OSO the data warehouse, you will need to request an API key. Include the following in your environmental variables to make sure you can access the data warehouse using the `oso_db` script:

```
DB_HOST=
DB_PORT=
DB_NAME=
DB_USER=
DB_PASSWORD=
```