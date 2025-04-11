# Insights  [![License: Apache 2.0][license-badge]][license]

[license]: https://opensource.org/license/apache-2-0/
[license-badge]: https://img.shields.io/badge/License-Apache2.0-blue.svg

This repository contains insights and exploratory data analysis on the health of open source software ecosystems. 

You can also find our folder of public Colab notebooks, [here](https://drive.google.com/drive/folders/1mzqrSToxPaWhsoGOR-UVldIsaX1gqP0F).

Notebooks are included so others can get inspiration and understand/improve upon our analysis. Where practical, copies of data used to generate insights has been saved in CSV or JSON format. However, many of the notebooks rely on direct queries to the data warehouse and therefore will not run locally without a live connection. Note: not all of these notebooks are actively maintained, so some queries may go stale over time.

## pyoso

You can access the full OSO data lake via our `pyoso` Python library.

The following boiler plate is helpful for starting a new notebook that uses pyoso.

```
from dotenv import load_dotenv
import os
import pandas as pd
from pyoso import Client

load_dotenv()
OSO_API_KEY = os.environ['OSO_API_KEY']
client = Client(api_key=OSO_API_KEY)

client.to_pandas("SELECT * FROM models_v0 LIMIT 5")
```

Here are more detailed steps if it's your first time using pyoso.

## Getting Started

> [!IMPORTANT]  
> The OSO data warehouse has evolved considerably since the start of this project. We have kept old notebooks (eg, that connect to BigQuery directly) for reference and inspiration. Currently, we strongly recommend all users to access data via pyoso.

### Generate an API key

First, go to [www.opensource.observer](https://www.opensource.observer) and create a new account.

If you already have an account, log in. Then create a new personal API key:

1. Go to [Account settings](https://www.opensource.observer/app/settings)
2. In the "API Keys" section, click "+ New"
3. Give your key a label - this is just for you, usually to describe a key's purpose.
4. You should see your brand new key. **Immediately** save this value, as you'll **never** see it again after refreshing the page.
5. Click "Create" to save the key.

### Install pyoso

You can install pyoso using pip:

```bash
pip install pyoso
```

### Issue your first query

Here is a basic example of how to use pyoso:

```python
from pyoso import Client

# Initialize the client
os.environ["OSO_API_KEY"] = 'your_api_key'
client = Client()

# Fetch artifacts
query = "SELECT * FROM artifacts_v1 LIMIT 5"
artifacts = client.query(query)

print(artifacts)
```

Once things are working, we recommend saving your API key in your .env file.

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
