# OSO agent guide — Filecoin PGF & ecosystem data

You are a data analyst with access to the OSO data warehouse. This document is the single entry point for **Filecoin ecosystem analysis** — public goods funding, developer activity, onchain metrics, and network health.

**Live dashboard:** [oso.xyz/filecoin/Public-Goods-Funding](https://www.oso.xyz/filecoin/Public-Goods-Funding)
**Public repo:** [github.com/opensource-observer/insights](https://github.com/opensource-observer/insights)
**Dependency survey:** [dependency-survey.pages.dev](https://dependency-survey.pages.dev)
**OSS Directory:** [github.com/opensource-observer/oss-directory](https://github.com/opensource-observer/oss-directory) — canonical source for project slugs, repos, and onchain artifacts. To add or update a project, submit a PR to the [data/projects/](https://github.com/opensource-observer/oss-directory/tree/main/data/projects) directory.

---

## What can I ask?

This dataset answers questions like:

**Funding & ROI**
- How much total funding has project X received (public + private)?
- Which projects got the most ProPGF / RetroPGF / Impact Grant funding?
- What's the funding-to-developer ratio across projects?
- Which programs are deploying the most capital?

**Developer activity**
- How many active developers does project X have? Is that growing or shrinking?
- Which projects have the most commit activity? The most PR activity?
- Are developers sticking around or churning?

**Onchain impact**
- How much data has project X onboarded to Filecoin?
- Which onramps are growing fastest?
- What share of network onboarding does project X account for?
- How much block reward revenue flows through a project's storage providers?

**Dependencies & downstream impact**
- Which infrastructure projects have the most downstream dependents?
- If project X disappeared, how much onchain activity would be affected?
- What do teams say they depend on (from the dependency survey)?

**Milestones & progress (Karma)**
- What milestones has project X committed to?
- Which projects have completed milestones? Which are overdue?
- Show me the Karma profile for project X alongside its actual metrics.

**Network health**
- What's the current network power, daily onboarding, and FIL price?
- How has protocol revenue trended over the past quarter?

---

## Connection

### If you're using OSO Chat or a notebook on oso.xyz
The connection is automatic — just ask your question or write SQL directly.

### If you're using pyoso locally

```bash
uv add pyoso  # or: pip install pyoso
export OSO_API_KEY=<your_key>
```

```python
from pyoso import Client
client = Client()  # reads OSO_API_KEY from environment
df = client.to_pandas("SELECT * FROM filecoin.filpgf_public.projects LIMIT 10")
```

### Getting an API key

1. Sign up at [oso.xyz/start](https://www.oso.xyz/start)
2. Go to **Settings → API Keys** in the OSO app
3. Create a key scoped to the **Filecoin** organization

**Important:** Filecoin data lives under the `filecoin.*` namespace, which requires a Filecoin-scoped API key. The default `oso.*` namespace is publicly accessible, but `filecoin.*` tables are customer-scoped.

---

## SQL dialect

Use **Trino SQL**:

- `CAST(x AS VARCHAR)` not `SAFE_CAST`
- `DATE_TRUNC('month', dt)` not `DATE_TRUNC(dt, MONTH)`
- `COALESCE` not `IFNULL`
- `CURRENT_DATE - INTERVAL '30' DAY` for date math

---

## Schema overview

The Filecoin org has data organized in a layered DAG. A Filecoin-scoped API key gives access to all layers:

```
Ingested Data                    OSO Public Data
─────────────                    ───────────────
filecoin.data_portal.*           oso.oss_directory.*
filecoin.gsheets.*               oso.int_events__github_unified
filecoin.karma.*
filecoin.datacapstats.*
filecoin.onramp_dependency_scores.*
filecoin.token_prices.*
filecoin.karma_milestones.*
filecoin.attribution_registry.*

        ↓                                ↓

filecoin.staging_external.*      filecoin.staging_oso.*
        ↓                                ↓
              filecoin.entities.*
                     ↓
              filecoin.events.*
                     ↓
              filecoin.metrics.*
                     ↓
        filecoin.filpgf_public.*  ←  filecoin.roi.*
```

For most analysis, start with `filecoin.filpgf_public.*` (the mart layer). Go deeper into staging/entities/metrics when you need custom joins or granularity the marts don't expose.

---

## Discovering metrics

Rather than listing every metric here (they evolve), query the catalog directly:

```sql
SELECT
  metric_name,
  metric_display_name,
  metric_units,
  metric_description,
  metric_category
FROM filecoin.filpgf_public.metric_catalog
ORDER BY metric_category, metric_name
```

Metric categories include: `github`, `client_onchain`, `sp_onchain`, `funding`, `downstream`, `network`, `filecoin_pay`, `warm_storage`, `datacap`.

To see what snapshot/lifetime metrics exist for a specific project:

```sql
SELECT metric_name, amount, metric_units
FROM filecoin.filpgf_public.key_metrics_by_project
WHERE oso_project_slug = 'lighthouse'
ORDER BY metric_name
```

**Note:** Snapshot metrics in `key_metrics_by_project` are prefixed with `latest_` (eg `latest_commits`, `latest_active_developers_28d`) or `total_` (eg `total_funding_usd`, `total_sp_onboarded_tibs`). Timeseries metrics in `timeseries_metrics_by_project` use bare names (eg `commits`, `active_developers_28d`). The dependency survey assigns importance scores from 0 (no dependency) to 5 (critical dependency) per pair.

---

## Key tables (mart layer)

All tables below are in the `filecoin.filpgf_public` schema. The universal join key is `oso_project_slug`, which comes from [oss-directory](https://github.com/opensource-observer/oss-directory/tree/main/data/projects) — each project's YAML filename (minus `.yaml`) is its slug.

| Table | Grain | Use when you want to... |
|-------|-------|------------------------|
| `projects` | project | List tracked projects, get display names and metadata |
| `artifacts_by_project` | (project, artifact) | See repos, onchain client IDs, and grant applications per project |
| `projects_to_projects` | (project, source, name) | Cross-system identity bridges (OSSD ↔ Karma ↔ Drips ↔ Data Portal) |
| `metric_catalog` | metric | Look up metric definitions, units, and categories |
| `timeseries_metrics_by_project` | (project, date, interval, metric) | Trend any metric over time for a project |
| `key_metrics_by_project` | (project, metric) | Get latest snapshot + lifetime totals per project |
| `timeseries_metrics_by_artifact` | (artifact, date, interval, metric) | Drill down to individual repos or onchain artifacts |
| `timeseries_metrics_by_program` | (program, date, interval, metric) | Compare funding programs over time |
| `key_metrics_by_program` | (program, metric) | Snapshot totals per funding program |
| `timeseries_metrics_by_network` | (date, interval, metric) | Network-wide Filecoin health trends |
| `key_metrics_by_network` | metric | Latest network-level snapshots |
| `key_metrics_by_artifact` | (artifact, metric) | Drill down to individual repos or onchain artifacts |

---

## Key workflow: Karma milestones → project metrics

A common workflow is checking a project's Karma milestones against its actual performance data:

**Step 1: Find a project's Karma profile via the bridge table**

The bridge table maps `oso_project_slug` to `karma_slug` and `karma_title`:

```sql
SELECT
  k.karma_slug,
  k.karma_title,
  k.oso_project_slug
FROM filecoin.entities.bridge_karma_to_oso AS k
WHERE k.oso_project_slug = 'secured-finance'
```

**Step 2: Get milestones using the `karma_slug` from step 1**

```sql
SELECT
  m.project_title,
  m.milestone_title,
  m.current_status,
  m.ends_at,
  m.status_updated_at
FROM filecoin.karma_milestones.milestones AS m
WHERE m.karma_slug = 'secured-finance'  -- use karma_slug from step 1
ORDER BY m.ends_at
```

**Step 3: Pull actual metrics to compare against milestones**

Snapshot metrics in `key_metrics_by_project` use `latest_` and `total_` prefixes:

```sql
SELECT
  metric_name,
  amount,
  metric_units
FROM filecoin.filpgf_public.key_metrics_by_project
WHERE oso_project_slug = 'secured-finance'
  AND metric_name IN (
    'total_funding_usd',
    'total_funding_fil',
    'latest_active_developers_28d',
    'total_sp_onboarded_tibs',
    'total_sp_block_rewards_usd',
    'latest_commits'
  )
```

**Step 4: Show the trend**

Timeseries metrics use bare names (no `latest_`/`total_` prefix):

```sql
SELECT
  sample_date,
  metric_name,
  amount
FROM filecoin.filpgf_public.timeseries_metrics_by_project
WHERE oso_project_slug = 'secured-finance'
  AND metric_name IN ('commits', 'active_developers_28d', 'sp_onboarded_data_tibs')
  AND time_interval = 'monthly'
ORDER BY sample_date
```

---

## Reference: full table inventory

Most analysis uses the mart layer above. The sections below document the full DAG for when you need to go deeper — custom joins, raw data, or entity resolution logic.

### Upstream data sources

#### Ingested datasets (`filecoin.data_portal.*`)

Raw Filecoin Data Portal tables — snapshot and daily metrics from the network.

| Table | Rows | Description |
|-------|------|-------------|
| `filecoin.data_portal.clients` | ~5k | Client snapshot stats (datacap, deals, providers) |
| `filecoin.data_portal.storage_providers` | ~7.9k | SP snapshot stats (power, sectors, balance) |
| `filecoin.data_portal.daily_clients_metrics` | ~3.2M | Daily client-level metrics (market deals only) |
| `filecoin.data_portal.daily_network_metrics` | ~2k | Daily network-wide metrics (126 columns) |
| `filecoin.data_portal.daily_filecoin_pay_operators_metrics` | varies | Daily Filecoin Pay operator metrics |
| `filecoin.data_portal.filecoin_pay_rails` | varies | Filecoin Pay payment rails |
| `filecoin.data_portal.pdp_service_providers` | varies | PDP (warm storage) service providers |
| `filecoin.data_portal.warm_storage_datasets` | varies | Warm storage dataset activity |

#### Ingested datasets (`filecoin.karma.*`, `filecoin.datacapstats.*`)

| Table | Description |
|-------|-------------|
| `filecoin.karma.registry` | Karma ProPGF project registry (~34 projects, links, metadata) |
| `filecoin.karma_milestones.milestones` | ProPGF grant milestones from Karma GAP API |
| `filecoin.datacapstats.verified_clients` | DataCapStats verified client records |
| `filecoin.datacapstats.verifiers` | DataCapStats allocator/verifier records |
| `filecoin.datacapstats.filplus_stats` | Network-level FilPlus statistics |

#### Google Sheets connections (`filecoin.gsheets.*`)

| Table | Description |
|-------|-------------|
| `filecoin.gsheets.onchain_artifacts` | Curated onchain artifact registry (client IDs, SP IDs, allocator IDs, wallets) |
| `filecoin.gsheets.public_grants_registry` | Public grants: ProPGF, Impact Grants, Hackathons (~132 rows) |
| `filecoin.gsheets.private_grants_registry_consolidated` | Private grants registry |

#### Static models

| Table | Description |
|-------|-------------|
| `filecoin.token_prices.token_prices` | Daily FIL/USD prices (Yahoo Finance + CoinGecko) |
| `filecoin.attribution_registry.artifact_registry` | Onchain artifact→entity mapping for onramp attribution |
| `filecoin.attribution_registry.client_sp_mapping` | Client→SP mappings from DataCapStats |
| `filecoin.onramp_dependency_scores.survey_submissions` | Dependency survey responses (0-5 importance scores from onramp teams) |

---

### Staging layer

Materialized, filtered, and cast views of the raw data. Useful when you need more granularity than the marts.

#### `filecoin.staging_oso.*` (OSO public data, scoped to Filecoin)

| Table | Description |
|-------|-------------|
| `staging__oso__projects_by_collection` | Root of DAG — projects in `filecoin-*` collections |
| `staging__oso__projects` | Filecoin project metadata |
| `staging__oso__artifacts_by_project` | All artifact types per project |
| `staging__oso__repositories` | GitHub repo metadata (stars, forks, language, license) |
| `staging__oso__github_events` | GitHub events for tracked repos, >= 2024-01-01 |

#### `filecoin.staging_external.*` (external sources)

| Table | Description |
|-------|-------------|
| `staging__data_portal__allocators` | Allocator→client mapping with metadata |
| `staging__data_portal__clients` | Client snapshot stats |
| `staging__data_portal__client_providers` | Client→SP mapping |
| `staging__data_portal__daily_clients` | Deduplicated daily client metrics, >= 2024-01-01 |
| `staging__data_portal__daily_network` | Daily network-wide metrics, >= 2024-01-01 |
| `staging__data_portal__daily_sp_metrics` | Deduplicated daily SP metrics (~150 days only) |
| `staging__data_portal__filecoin_pay_operators` | Filecoin Pay operator staging |
| `staging__data_portal__filecoin_pay_rails` | Filecoin Pay rails staging |
| `staging__data_portal__warm_storage` | Warm storage staging |
| `staging__drips__rpgf_applications` | Drips RetroPGF records with JSON extraction |
| `staging__drips__rpgf_support_items` | Per-support-item funding: wei→FIL conversion |
| `staging__gsheets__onchain_artifacts` | Curated onchain artifact registry |
| `staging__gsheets__public_grants` | Cleaned public grants with program mapping |
| `staging__gsheets__private_grants` | Cleaned private grants |
| `staging__karma__registry` | Karma ProPGF projects with flattened links |
| `staging__survey__submissions` | Dependency survey responses |
| `staging__survey__progress` | Survey completion progress |

---

### Derived layers

#### `filecoin.entities.*` (entity resolution)

| Table | Description |
|-------|-------------|
| `registry_ossd` | ~337 OSSD projects in Filecoin collections |
| `registry_propgf` | ~34 Karma ProPGF projects |
| `registry_retropgf` | ~111 Drips RetroPGF applications with earned amounts |
| `registry_data_portal` | ~523 active Data Portal entities |
| `bridge_karma_to_oso` | Karma slug → OSSD project mapping |
| `bridge_drips_to_oso` | Drips repo → OSSD mapping (override for renames) |
| `bridge_data_portal_to_oso` | Data Portal entity → OSSD slug mapping |
| `projects_canonical` | Unified project list across all registries |
| `projects_bridged` | Cross-system identity mappings |
| `artifacts_github_repos` | GitHub repos per project |
| `artifacts_onchain` | Onchain artifacts (client IDs, SP IDs, allocator IDs, wallets) |
| `artifacts_grant_applications` | Grant applications per (project, program) |
| `dependency_classification` | Project type: pod, sp_operator, onramp, infrastructure, ecosystem_support |
| `dependency_matrix` | Weighted dependency edges from survey |

#### `filecoin.events.*`

| Table | Description |
|-------|-------------|
| `events_github` | GitHub events for tracked repos |
| `events_onchain` | Daily client metrics joined to artifacts for entity resolution |
| `events_public_funding` | RetroPGF + ProPGF + Impact Grants + Hackathons |
| `events_private_funding` | Private grant events |

#### `filecoin.metrics.*`

| Table | Grain | Description |
|-------|-------|-------------|
| `metrics_github` | (project, date) | Daily event counts + 28d rolling unique actors |
| `metrics_onchain` | (entity/project, date) | Client-side + SP-side attributed metrics |
| `metrics_downstream` | (project, date) | Weighted downstream impact via dependency matrix |
| `metrics_public_funding` | (project, date, program) | Daily funding amounts per program |
| `metrics_private_funding` | (project, month) | Monthly boolean for active private grants |
| `metrics_network_level` | (date) | Network-wide: power, gas, revenue, token economics |
| `metrics_filecoin_pay` | (date, entity, metric) | Filecoin Pay ARR and warm storage per operator |
| `metrics_warm_storage` | (project, date) | Warm storage activity per PDP provider |
| `metrics_datacap` | (entity) | Data Portal snapshot stats: onramp activity, allocator datacap |

#### `filecoin.roi.*`

| Table | Description |
|-------|-------------|
| `all_funding_events` | Unified funding events, USD-normalized via token_prices |
| `roi_project_summary` | Per-project: total funding (FIL + USD) + impact metrics snapshot |

---

## Starter queries

**List all tracked projects:**

```sql
SELECT
  oso_project_slug,
  display_name
FROM filecoin.filpgf_public.projects
ORDER BY display_name
```

**Top funded projects (lifetime totals):**

```sql
SELECT
  p.oso_project_slug,
  p.display_name,
  MAX(CASE WHEN k.metric_name = 'total_funding_usd' THEN k.amount END) AS total_usd,
  MAX(CASE WHEN k.metric_name = 'total_funding_fil' THEN k.amount END) AS total_fil,
  MAX(CASE WHEN k.metric_name = 'funding_disbursement_count' THEN k.amount END) AS disbursements
FROM filecoin.filpgf_public.projects AS p
INNER JOIN filecoin.filpgf_public.key_metrics_by_project AS k
  ON p.oso_project_slug = k.oso_project_slug
WHERE k.metric_name IN ('total_funding_usd', 'total_funding_fil', 'funding_disbursement_count')
GROUP BY p.oso_project_slug, p.display_name
ORDER BY total_usd DESC NULLS LAST
LIMIT 30
```

**Monthly developer activity across all Filecoin projects:**

```sql
SELECT
  sample_date,
  metric_name,
  SUM(amount) AS total
FROM filecoin.filpgf_public.timeseries_metrics_by_project
WHERE metric_name IN ('commits', 'active_developers_28d')
  AND time_interval = 'monthly'
GROUP BY sample_date, metric_name
ORDER BY sample_date
```

**Funding by program over time:**

```sql
SELECT
  sample_date,
  metric_name,
  SUM(amount) AS total
FROM filecoin.filpgf_public.timeseries_metrics_by_program
WHERE metric_name IN ('propgf_amount_usd', 'retropgf_amount_fil', 'impact_grants_amount_fil')
  AND time_interval = 'monthly'
GROUP BY sample_date, metric_name
ORDER BY sample_date
```

**Network health (last 30 days):**

```sql
SELECT
  sample_date,
  metric_name,
  amount
FROM filecoin.filpgf_public.timeseries_metrics_by_network
WHERE metric_name IN (
  'network_raw_power_pibs',
  'network_daily_onboarding_tibs',
  'fil_price_usd',
  'network_block_rewards_fil'
)
AND time_interval = 'daily'
AND sample_date >= CURRENT_DATE - INTERVAL '30' DAY
ORDER BY sample_date, metric_name
```

**Project ROI: funding vs impact:**

```sql
SELECT
  p.oso_project_slug,
  p.display_name,
  MAX(CASE WHEN k.metric_name = 'total_funding_usd' THEN k.amount END) AS funding_usd,
  MAX(CASE WHEN k.metric_name = 'latest_active_developers_28d' THEN k.amount END) AS active_devs,
  MAX(CASE WHEN k.metric_name = 'total_sp_onboarded_tibs' THEN k.amount END) AS sp_data_tibs
FROM filecoin.filpgf_public.projects AS p
INNER JOIN filecoin.filpgf_public.key_metrics_by_project AS k
  ON p.oso_project_slug = k.oso_project_slug
WHERE k.metric_name IN ('total_funding_usd', 'latest_active_developers_28d', 'total_sp_onboarded_tibs')
GROUP BY p.oso_project_slug, p.display_name
HAVING MAX(CASE WHEN k.metric_name = 'total_funding_usd' THEN k.amount END) > 0
ORDER BY funding_usd DESC
```

---

## Important notes

- **Timeseries data starts from 2024-01-01.** Lifetime totals in `key_metrics_by_project` reflect post-2024 activity only.
- **DDO onramps (Ramo, Titan) bypass the deal pipeline.** Their `client_*` metrics are NULL — only `sp_*` metrics capture their activity.
- **Amounts are in native currency** (FIL or USD depending on the metric). Check `metric_units` in the catalog.
- **Private funding is boolean only.** The `received_private_grant` metric shows whether a project had an active private grant (1/0), but amounts are not exposed publicly.
- **All `filecoin.*` tables are accessible** with a Filecoin-scoped API key — including staging, entities, metrics, and raw ingested data. Start with `filpgf_public` for most analysis; go deeper when you need custom joins.

---

## Joining with OSO public data

Filecoin projects are tracked in [oss-directory](https://github.com/opensource-observer/oss-directory). You can join Filecoin data with the public `oso.*` namespace using `oso_project_slug`:

```sql
SELECT
  fp.oso_project_slug,
  fp.display_name,
  op.description
FROM filecoin.filpgf_public.projects AS fp
INNER JOIN oso.projects_v1 AS op
  ON fp.oso_project_slug = op.project_name
  AND op.project_source = 'OSS_DIRECTORY'
```

This gives you access to the full OSO metrics ecosystem (code metrics, onchain activity, funding from other sources) alongside the Filecoin-specific data.
