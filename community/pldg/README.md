# PLDG Community

Welcome! This directory contains data analysis notebooks created by Protocol Labs Developer Guild (PLDG) contributors.

Each notebook audits a different part of the OSO data warehouse, documenting data pipelines and performing quality checks.

**Contributing?** See [CONTRIBUTING.md](CONTRIBUTING.md) for submission guidelines.

---

## Quick Start

### Prerequisites

- Python 3.10+ with `uv` installed ([install uv](https://docs.astral.sh/uv/))
- OSO API key from [oso.xyz](https://www.oso.xyz/app/settings)
- Knowledge of SQL and Python for data science

### Setup

**Option A: Clone the repo** (recommended to see examples)

```bash
git clone https://github.com/opensource-observer/insights.git
cd insights/community/pldg
uv sync
echo "OSO_API_KEY=your_api_key_here" > .env
uv run marimo edit health_check_template.py
```

**Option B: Standalone setup** (minimal)

```bash
mkdir my-project && cd my-project
uv init --no-workspace
uv add marimo pyoso plotly pandas
curl -o health_check_template.py https://raw.githubusercontent.com/opensource-observer/insights/main/community/pldg/health_check_template.py
echo "OSO_API_KEY=your_api_key_here" > .env
uv run marimo edit health_check_template.py
```

**Get your API key:** Visit [oso.xyz/app/settings](https://www.oso.xyz/app/settings) → API Keys → "+ New"

---

## Understanding OSO Data

### Table Naming Convention

OSO uses prefixes and suffixes to indicate pipeline stages:

| Pattern | Stage | Example |
|---------|-------|---------|
| `oso.stg_[source]__[table]` | **Staging** (raw data) | `oso.stg_github__events` |
| `oso.int_[model]` | **Intermediate** (transformed) | `oso.int_events_daily__github` |
| `oso.[model]_v0` or `_v1` | **Mart** (final, versioned) | `oso.timeseries_metrics_by_project_v0` |

### Available Data Sources

**Staging sources** at `oso.stg_<source>__*`:
- **github** - Events, repos, users from [GitHub Archive](https://www.gharchive.org/)
- **ossd** - Projects and collections from [OSS Directory](https://github.com/opensource-observer/oss-directory)
- **opendevdata** - Developer data from [Electric Capital](https://github.com/electric-capital/open-dev-data)
- **op-atlas** - Optimism projects from [OP Atlas](https://atlas.optimism.io/)
- **defillama** - DeFi metrics from [DefiLlama](https://defillama.com/)
- **l2beat** - Layer 2 metrics from [L2Beat](https://l2beat.com/)
- **superchain** - Superchain data from [Optimism](https://docs.optimism.io/app-developers/tools/data/)

[See full list →](https://github.com/opensource-observer/oso/tree/main/warehouse/oso_sqlmesh/models/staging)

**Key mart models:**
- `oso.projects_v1` - Project metadata
- `oso.artifacts_by_project_v1` - Repos and packages by project
- `oso.timeseries_metrics_by_project_v0` - Time-series metrics
- `oso.metrics_v0` - Metric definitions

---

## Resources

**OSO Documentation**
- [Main docs](https://docs.oso.xyz) - Platform documentation
- [Data models](https://docs.oso.xyz/guides/data-model/) - Understanding OSO's architecture
- [pyoso quickstart](https://docs.oso.xyz/get-started/) - Query the warehouse

**Tools**
- [Marimo docs](https://docs.marimo.io/) - Reactive Python notebooks
- [Trino SQL](https://trino.io/docs/current/sql.html) - SQL dialect used by OSO

**Community**
- [Discord](https://www.oso.xyz/discord) - Join #pldg
- [GitHub](https://github.com/opensource-observer/oso) - OSO repository

---

**Happy exploring!** We're excited to see what insights you discover.
