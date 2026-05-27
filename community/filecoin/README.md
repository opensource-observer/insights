# Filecoin Pro PGF — Community Tools

Tools for analyzing and evaluating Filecoin Pro PGF grants using OSO data.

## Quick Start

```bash
# Set your Filecoin-scoped API key
export OSO_API_KEY=<your_filecoin_key>

# Serve the metric selection form locally
cd examples
python3 -m http.server 8765
# Open http://localhost:8765/propgf-metric-selection.html
```

## Directory Structure

```
filecoin/
├── guides/                              # Framework docs and agent prompts
│   ├── propgf-metric-selection.md       # Metric attribution framework
│   ├── propgf-milestone-review.md       # Agent prompt: track funded grants vs milestones
│   ├── propgf-applicant-dossier.md      # Agent prompt: evaluate new applications
│   └── karma-api.md                     # Karma GAP API reference
├── scripts/                             # Data scripts
│   ├── select_propgf_metrics.py       # Refresh metric selection form data
│   ├── fetch_karma.py                   # Fetch grant data from Karma API
│   └── execute_oso_query.py           # Run ad-hoc SQL against the warehouse
├── examples/                            # Interactive tools
│   └── propgf-metric-selection.html     # Metric selection form (self-contained)
├── skills.md                            # Agent entry point — data model reference
└── README.md                            # This file
```

### guides/

Framework documentation and agent prompts. Start with [propgf-metric-selection.md](guides/propgf-metric-selection.md) to understand how metrics map to KPIs, entity types, and direct/indirect attribution.

### scripts/

Data scripts that query the OSO warehouse or external APIs. All require `OSO_API_KEY` unless noted. Run [select_propgf_metrics.py](scripts/select_propgf_metrics.py) to refresh the metric selection form with the latest data.

### examples/

Interactive HTML tools. Serve locally with any static HTTP server. The [metric selection form](examples/propgf-metric-selection.html) is self-contained (no build step, no dependencies).

## Data Requirements

All tools require a **Filecoin-scoped OSO API key** (`OSO_API_KEY`). This grants access to the `filecoin.*` namespace in the data warehouse. See [skills.md](skills.md) for the full table reference.
