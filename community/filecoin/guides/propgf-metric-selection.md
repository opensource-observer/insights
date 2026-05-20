# Pro PGF Metric Selection Framework

A framework for Filecoin Pro PGF grant recipients to identify which impact metrics they want to be evaluated against. Includes an interactive form for browsing, selecting, and exporting metric selections.

## The Problem

Pro PGF funds a diverse set of projects — onramps that onboard data directly, infrastructure that powers other projects, and ecosystem tools with indirect impact. Not every metric applies to every project, and the type of impact claim (direct vs indirect) depends on what the project actually does. We need a structured way for projects to pick their metrics and for reviewers to verify them.

## How It Works

### Entity Types

Every Pro PGF project is classified into one of five entity types based on what it does in the Filecoin network:

| Entity Type | What It Means | Example Projects |
|---|---|---|
| **onramp** | Directly onboards data to Filecoin via verified deals | CIDgravity, Lighthouse, Storacha |
| **sp_operator** | Operates storage providers (miners) | Titan Network, Aurora, Akave |
| **infrastructure** | Builds core protocol software that others depend on | Lotus, Forest, IPNI, Curio |
| **ecosystem_support** | Provides tooling, analytics, or community services | Oku Trade, Probe Lab, Venus |
| **unclassified** | Not yet classified via the dependency survey | chainfee, EverMedia Vault |

Entity type determines the **default attribution** for each metric — whether a project claims direct or indirect impact.

### Attribution Methods

- **Direct**: The project's own onchain artifacts (client IDs, miner IDs, payment rails) generate the metric. Fully verifiable from the Data Portal.
- **Indirect**: The project's impact flows through other projects that depend on it. Measured via the dependency survey combined with onchain data from downstream dependents.

### KPI Alignment

Every metric maps to one of Filecoin's three strategic objectives:

1. **Drive Paid Onchain Deals** ($20M ARR target) — Filecoin Pay ARR, warm storage datasets, verified data onboarded
2. **Strengthen Network Profitability** (revenue covers 33%+ of costs) — SP block rewards, data onboarding, network share
3. **Scale Flagship Client Adoption** (20 high-profile brands) — unique clients/providers, downstream entity counts

A fourth category, **Developer Activity**, covers baseline "proof of work" metrics from GitHub (commits, active developers, contributors).

### Metric Sources

Each metric comes from a specific data source:

| Source Label | What It Covers |
|---|---|
| **Data Portal** | Onchain metrics from the Filecoin Data Portal — verified claims, SP data, block rewards |
| **GitHub** | Developer activity from GitHub Archive — commits, PRs, issues, active developers |
| **Survey + Data Portal** | Dependency survey results combined with onchain data from downstream projects |
| **Filecoin Pay** | Revenue and payer data from Filecoin Pay payment rails |
| **Warm Storage** | PDP warm storage provider datasets and payers |

## Using the Form

### Setup

You need a Filecoin-scoped OSO API key. The form ships with data pre-loaded, but you can regenerate it with fresh data using the rebuild script.

To view the form:

```bash
cd community/filecoin
python3 -m http.server 8765
# Open http://localhost:8765/propgf-metric-selection.html
```

### Workflow

1. **Select a grant** from the dropdown. Grants are organized by batch (Batch 1: Sep-Dec 2025, Batch 2: Feb 2026). Grants without matched OSO data are grayed out.

2. **Review the defaults**. The form pre-selects 3 recommended metrics based on entity type:
   - **Onramps/SP operators**: Direct onchain metrics (data onboarded, block rewards, SP count)
   - **Infrastructure**: Downstream impact metrics (downstream block rewards, downstream entity count, active developers)
   - **Ecosystem support**: Downstream reach and dev activity (downstream entities, downstream onramps, active developers)

3. **Adjust selections**. Click any metric row to select or deselect it (max 3). Each row shows:
   - Display name and data source
   - Attribution type (DIRECT or INDIRECT)
   - Sparkline trend for the evaluation period
   - Latest value with units

4. **Explore other metrics**. The "Other Metrics" section at the bottom shows metrics that have data for this project but aren't in the default set for its entity type. Selecting one of these requires a written justification explaining the link.

5. **Export**. Click "Copy Selections as JSON" to get structured output, or "View as Table" to see the flat format matching the target schema.

### Export Schema

The JSON export includes:

```json
{
  "oso_project_slug": "cidgravity",
  "entity_type": "onramp",
  "grant_name": "CIDgravity gateway",
  "batch": "Batch1",
  "funded_amount": 50000,
  "selected_at": "2026-05-20",
  "selections": [
    {
      "metric_name": "client_onboarded_data_tibs",
      "metric_display_name": "Client Data Onboarded",
      "metric_units": "TiB",
      "attribution_method": "direct",
      "justification": null,
      "latest_value": 137.13,
      "timeseries": [
        {"date": "2026-02-01", "value": 100.5},
        {"date": "2026-03-01", "value": 120.3},
        {"date": "2026-04-01", "value": 137.13}
      ]
    }
  ]
}
```

The "View as Table" output matches the target evaluation schema:

| Column | Description |
|---|---|
| `metric_name` | Machine-readable metric identifier |
| `metric_display_name` | Human-readable name |
| `metric_units` | Units (count, TiB, FIL, USD, pct, USDfc) |
| `attribution_method` | `direct` or `indirect` |
| `date` | Monthly observation date |
| `value` | Metric value for that month |

## Metric Reference

### Direct Metrics (onramps, SP operators)

| Metric | Units | KPI | Source |
|---|---|---|---|
| `client_onboarded_data_tibs` | TiB | Onchain Deals | Data Portal |
| `client_deals` | count | Onchain Deals | Data Portal |
| `client_unique_providers` | count | Client Adoption | Data Portal |
| `sp_block_rewards_fil` | FIL | Network Profitability | Data Portal |
| `sp_block_rewards_usd` | USD | Network Profitability | Data Portal |
| `sp_onboarded_data_tibs` | TiB | Network Profitability | Data Portal |
| `sp_count` | count | Network Profitability | Data Portal |
| `sp_blocks_mined` | count | Network Profitability | Data Portal |
| `sp_verified_data_onboarded_tibs` | TiB | Onchain Deals | Data Portal |
| `sp_verified_claims` | count | Onchain Deals | Data Portal |
| `filecoin_pay_arr_usdfc` | USDfc | Onchain Deals | Filecoin Pay |
| `filecoin_pay_unique_payers` | count | Onchain Deals | Filecoin Pay |
| `warm_storage_active_datasets` | count | Onchain Deals | Warm Storage |
| `warm_storage_unique_payers` | count | Onchain Deals | Warm Storage |

### Indirect Metrics (infrastructure, ecosystem support)

| Metric | Units | KPI | Source |
|---|---|---|---|
| `downstream_entity_count` | count | Client Adoption | Survey + Data Portal |
| `downstream_onramp_count` | count | Client Adoption | Survey + Data Portal |
| `downstream_sp_block_rewards_fil` | FIL | Network Profitability | Survey + Data Portal |
| `downstream_sp_block_rewards_usd` | USD | Network Profitability | Survey + Data Portal |
| `downstream_sp_onboarded_data_tibs` | TiB | Network Profitability | Survey + Data Portal |
| `downstream_sp_count` | count | Network Profitability | Survey + Data Portal |
| `downstream_sp_verified_data_tibs` | TiB | Onchain Deals | Survey + Data Portal |
| `downstream_sp_verified_claims` | count | Onchain Deals | Survey + Data Portal |

### Developer Activity (all entity types)

| Metric | Units | Source |
|---|---|---|
| `active_developers_28d` | count | GitHub |
| `active_contributors_28d` | count | GitHub |
| `commits` | count | GitHub |

## Regenerating the Data

The form embeds its data as JSON. To refresh with the latest from the warehouse:

```bash
# Requires: pip install pyoso
# Requires: export OSO_API_KEY=<your_filecoin_scoped_key>
python3 select_propgf_metrics.py
```

This queries `filecoin.filpgf_public.timeseries_metrics_by_project` for all Pro PGF projects and updates the embedded data in the HTML file.

## Data Model

The metrics come from the `filecoin.filpgf_public.*` mart models in the OSO data warehouse:

- **`timeseries_metrics_by_project`** — Monthly timeseries for all metrics, keyed by OSO project slug
- **`metric_catalog`** — Metric definitions (display name, units, aggregation method, source)
- **`key_metrics_by_project`** — Point-in-time snapshot (latest values, lifetime totals)
- **`projects`** — Project registry with entity type classification

For more on the data pipeline, see the [OSO documentation](https://docs.oso.xyz).
