# Filecoin Developer Lifecycle Analysis

Interactive notebooks for exploring developer activity and lifecycle metrics across the Protocol Labs Network (PLN) ecosystem.

## Quick Start

### 1. Set up environment

```bash
# Create virtual environment and install dependencies
uv sync
```

### 2. Configure API key

Copy the example env file and add your OSO API key:

```bash
cp .env.example .env
# Edit .env and replace 'your-api-key-here' with your actual key
```

Get your API key from [opensource.observer](https://www.opensource.observer/).

### 3. Run a notebook

```bash
# Edit mode (interactive development)
uv run marimo edit notebooks/filecoin-data-tour.py

# App mode (read-only presentation)
uv run marimo run notebooks/filecoin-data-tour.py
```

## Notebooks

| Notebook | Type | Description |
|----------|------|-------------|
| `filecoin-data-tour.py` | Interactive Docs | Tour of Filecoin-relevant datasets and tables |
| `pln-ecosystem-health.py` | Strategic Insights | PLN ecosystem health with 5 quantified insights |
| `growth-trends-analysis.py` | Strategic Insights | YoY growth, momentum, and forecasting |
| `developer-funnel-dashboard.py` | Dashboard | Developer lifecycle funnel tracking |
| `repository-explorer-dashboard.py` | Dashboard | Repository-level metrics explorer |

## Data Sources

These notebooks query the [OSO](https://opensource.observer/) data warehouse via `pyoso`. Key tables include:

- `collections_v1` - Collection definitions (PLN, Filecoin Core, Filecoin Builders)
- `projects_v1` - Project metadata
- `projects_by_collection_v1` - Project-to-collection mappings
- `artifacts_by_project_v1` - Repository-to-project mappings
- `timeseries_metrics_by_collection_v0` - Time-series metrics by collection
- `timeseries_metrics_by_project_v0` - Time-series metrics by project
- `metrics_v0` - Metric definitions and metadata

## Lifecycle Metrics

Contributors are classified by monthly activity level:

| State | Definition |
|-------|------------|
| Full-time | 10+ days of activity per month |
| Part-time | 1-9 days of activity per month |
| First-time | First contribution in current period |
| Churned | No activity after being previously active |
| Reactivated | Returned after a gap in activity |

## Resources

- [OSO Documentation](https://docs.opensource.observer/)
- [Pyoso Getting Started](https://docs.opensource.observer/docs/get-started/python)
- [Marimo Documentation](https://docs.marimo.io/)

## Additional Documentation

See the `docs/` folder for:
- **Guides/** - Best practices for creating notebooks
- **Templates/** - Starter templates for different notebook types
- **Notebook Examples/** - Reference implementations
