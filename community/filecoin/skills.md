# Filecoin PGF & ecosystem data

This is the entry point for Filecoin ecosystem analysis: public goods funding, developer activity, onchain metrics, and network health. All data is queryable via Trino SQL through the OSO data warehouse.

## Access tiers

Data access depends on the user's role in the OSO platform. Default to COMMUNITY unless the user explicitly requests tables from a deeper layer or states they have org-level access.

```
COMMUNITY (any OSO user who has subscribed to the filecoin.filpgf_public.* datasets):
  filecoin.filpgf_public.*    — mart layer, pre-joined analysis views
  oso.*                        — public OSO data (projects, metrics, events)

FILECOIN (any OSO user who is a member of the `filecoin` org space on OSO):
  filecoin.*                   — all tables: staging, entities, events, metrics, and raw ingested data
```

When generating queries, use `filecoin.filpgf_public.*` and `oso.*` tables. Only use deeper layers (staging, entities, events, metrics) if the user has FILECOIN access and the mart layer cannot answer the question.

## Resources

- Live dashboard: https://www.oso.xyz/filecoin/Public-Goods-Funding
- Public repo: https://github.com/opensource-observer/insights
- Dependency survey: https://dependency-survey.pages.dev
- OSS Directory: https://github.com/opensource-observer/oss-directory — canonical source for project slugs, repos, and onchain artifacts
- Karma GAP API: see [guides/karma-api.md](guides/karma-api.md) — direct API access to real-time milestone and grant data (no API key needed)
- Metric selection framework: see [guides/propgf-metric-selection.md](guides/propgf-metric-selection.md) — how metrics map to KPIs, entity types, and attribution claims

---

## Connection

On OSO Chat or an oso.xyz notebook, the connection is automatic.

For local use with pyoso:

```bash
uv add pyoso  # or: pip install pyoso
export OSO_API_KEY=<your_key>
```

```python
from pyoso import Client
client = Client()
df = client.to_pandas("SELECT * FROM filecoin.filpgf_public.projects LIMIT 10")
```

API key setup: sign up at https://www.oso.xyz/start, go to Settings > API Keys, create a key scoped to the Filecoin organization. The `oso.*` namespace is publicly accessible; `filecoin.*` tables require a Filecoin-scoped key.

## SQL dialect

Use Trino SQL:
- `CAST(x AS VARCHAR)` not `SAFE_CAST`
- `DATE_TRUNC('month', dt)` not `DATE_TRUNC(dt, MONTH)`
- `COALESCE` not `IFNULL`
- `CURRENT_DATE - INTERVAL '30' DAY` for date math

---

## Schema overview

```
FILECOIN layer              Public layer
───────────────────             ────────────
filecoin.data_portal.*          oso.projects_v1
filecoin.karma.*                oso.artifacts_by_project_v1
filecoin.datacapstats.*         oso.int_events__github_unified
filecoin.token_prices.*         (etc.)
filecoin.karma_milestones.*
filecoin.attribution_registry.*
filecoin.onramp_dependency_scores.*
        |                               |
        v                               v
filecoin.staging_external.*     filecoin.staging_oso.*
        |                               |
        +-------> filecoin.entities.* <--+
                         |
                  filecoin.events.*
                         |
                  filecoin.metrics.*
                         |
             filecoin.filpgf_public.*
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^
             COMMUNITY layer — default for all queries
```

---

## COMMUNITY tables: filecoin.filpgf_public.*

All tables use `oso_project_slug` as the universal join key. Slugs come from OSS Directory — each project's YAML filename (minus `.yaml`) is its slug.

### Mart table reference

| Table | Grain | Description |
|-------|-------|-------------|
| `projects` | project | Tracked projects with display names and metadata |
| `artifacts_by_project` | (project, artifact) | Repos, onchain client IDs, and grant applications per project |
| `projects_to_projects` | (project, source, name) | Cross-system identity bridges: OSSD, Karma, Drips, Data Portal |
| `metric_catalog` | metric | Metric definitions, units, categories, and descriptions |
| `timeseries_metrics_by_project` | (project, date, interval, metric) | Any metric trended over time for a project |
| `key_metrics_by_project` | (project, metric) | Latest snapshot + lifetime totals per project |
| `timeseries_metrics_by_artifact` | (artifact, date, interval, metric) | Drill into individual repos or onchain artifacts |
| `key_metrics_by_artifact` | (artifact, metric) | Snapshot totals per individual artifact |
| `timeseries_metrics_by_pod` | (pod, date, interval, metric) | Metrics for FOC/LDO/Web2 pods over time |
| `key_metrics_by_pod` | (pod, metric) | Snapshot totals per pod (aggregated across member projects) |
| `timeseries_metrics_by_program` | (program, date, interval, metric) | Funding programs compared over time |
| `key_metrics_by_program` | (program, metric) | Snapshot totals per funding program |
| `timeseries_metrics_by_network` | (date, interval, metric) | Network-wide Filecoin health trends |
| `key_metrics_by_network` | metric | Latest network-level snapshots |

### Discovering metrics

Query the catalog rather than hardcoding metric names:

```sql
SELECT metric_name, metric_display_name, metric_units, metric_description, metric_category
FROM filecoin.filpgf_public.metric_catalog
ORDER BY metric_category, metric_name
```

Metric categories: `github`, `client_onchain`, `sp_onchain`, `funding`, `downstream`, `network`, `filecoin_pay`, `warm_storage`, `datacap`.

Naming conventions:
- `key_metrics_by_project`: snapshot metrics use `latest_` prefix (eg `latest_commits`, `latest_active_developers_28d`) or `total_` prefix (eg `total_funding_usd`, `total_sp_onboarded_tibs`)
- `timeseries_metrics_by_project`: bare names without prefix (eg `commits`, `active_developers_28d`)
- Dependency survey scores range from 0 (no dependency) to 5 (critical dependency) per pair

### Querying patterns

List all tracked projects:

```sql
SELECT oso_project_slug, display_name
FROM filecoin.filpgf_public.projects
ORDER BY display_name
```

Top funded projects (lifetime totals):

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

Monthly developer activity across all projects:

```sql
SELECT sample_date, metric_name, SUM(amount) AS total
FROM filecoin.filpgf_public.timeseries_metrics_by_project
WHERE metric_name IN ('commits', 'active_developers_28d')
  AND time_interval = 'monthly'
GROUP BY sample_date, metric_name
ORDER BY sample_date
```

Funding by program over time:

```sql
SELECT sample_date, metric_name, SUM(amount) AS total
FROM filecoin.filpgf_public.timeseries_metrics_by_program
WHERE metric_name IN ('propgf_amount_usd', 'retropgf_amount_fil', 'impact_grants_amount_fil')
  AND time_interval = 'monthly'
GROUP BY sample_date, metric_name
ORDER BY sample_date
```

Network health (last 30 days):

```sql
SELECT sample_date, metric_name, amount
FROM filecoin.filpgf_public.timeseries_metrics_by_network
WHERE metric_name IN (
  'network_raw_power_pibs', 'network_daily_onboarding_tibs',
  'fil_price_usd', 'network_block_rewards_fil'
)
AND time_interval = 'daily'
AND sample_date >= CURRENT_DATE - INTERVAL '30' DAY
ORDER BY sample_date, metric_name
```

Funding vs impact by project:

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

Pod-level metrics (FOC, LDO, Web2):

```sql
SELECT pod_slug, metric_name, member_count, sum_amount, avg_amount, metric_units
FROM filecoin.filpgf_public.key_metrics_by_pod
ORDER BY pod_slug, metric_name
```

### Karma milestones workflow

To check a project's milestones against its metrics:

1. Find cross-system identities (includes Karma slug) via the mart layer:

```sql
SELECT source, source_project_slug, source_project_name
FROM filecoin.filpgf_public.projects_to_projects
WHERE oso_project_slug = 'secured-finance'
```

2. Get milestone data from the Karma GAP API — see [guides/karma-api.md](guides/karma-api.md). No API key required, works for all users. FILECOIN tier users can also query milestones from the warehouse — see [FILECOIN: Karma milestones](#filecoin-karma-milestones-workflow) below.

3. Pull snapshot metrics from the mart layer:

```sql
SELECT metric_name, amount, metric_units
FROM filecoin.filpgf_public.key_metrics_by_project
WHERE oso_project_slug = 'secured-finance'
  AND metric_name IN (
    'total_funding_usd', 'total_funding_fil',
    'latest_active_developers_28d', 'total_sp_onboarded_tibs',
    'total_sp_block_rewards_usd', 'latest_commits'
  )
```

4. Show the trend (timeseries metrics use bare names, no prefix):

```sql
SELECT sample_date, metric_name, amount
FROM filecoin.filpgf_public.timeseries_metrics_by_project
WHERE oso_project_slug = 'secured-finance'
  AND metric_name IN ('commits', 'active_developers_28d', 'sp_onboarded_data_tibs')
  AND time_interval = 'monthly'
ORDER BY sample_date
```

### Joining with OSO public data

Join Filecoin data with the `oso.*` namespace using `oso_project_slug`:

```sql
SELECT fp.oso_project_slug, fp.display_name, op.description
FROM filecoin.filpgf_public.projects AS fp
INNER JOIN oso.projects_v1 AS op
  ON fp.oso_project_slug = op.project_name
  AND op.project_source = 'OSS_DIRECTORY'
```

### Caveats

- Timeseries data starts from 2024-01-01. Lifetime totals in `key_metrics_by_project` reflect post-2024 activity only.
- DDO onramps (Ramo, Titan) bypass the deal pipeline. Their `client_*` metrics are NULL — only `sp_*` metrics capture their activity.
- Amounts are in native currency (FIL or USD depending on the metric). Check `metric_units` in the catalog.
- Private funding is boolean only. The `received_private_grant` metric shows 1/0, not amounts.
- Pod metrics aggregate across member projects — they reflect the pod's collective footprint, not individual project metrics.

---

## FILECOIN tables

Everything below requires FILECOIN access (full `filecoin.*` namespace). Do not use these tables unless the user has confirmed org-level access or explicitly requested tables from these schemas.

### FILECOIN: Karma milestones workflow

For milestone data via the warehouse (rather than the Karma GAP API):

Step 1 — find a project's Karma profile:

```sql
SELECT k.karma_slug, k.karma_title, k.oso_project_slug
FROM filecoin.entities.bridge_karma_to_oso AS k
WHERE k.oso_project_slug = 'secured-finance'
```

Step 2 — get milestones:

```sql
SELECT m.project_title, m.milestone_title, m.current_status, m.ends_at, m.status_updated_at
FROM filecoin.karma_milestones.milestones AS m
WHERE m.karma_slug = 'secured-finance'
ORDER BY m.ends_at
```

Step 3 — check pod membership (for pod grants):

```sql
SELECT pod_slug, pod_display_name, member_slug, member_role, criticality
FROM filecoin.staging_external.staging__gsheets__pod_membership
WHERE pod_slug IN ('foc', 'ldo', 'web2')
ORDER BY pod_slug, criticality, member_slug
```

Pod grants map Karma slugs to pod slugs: `foc-filecoin-onachain-cloud` -> `foc`, `large-data-onboarding-pod-ldo-pod` -> `ldo`, `web2-object-storage-pod` -> `web2`.

### FILECOIN: Full table inventory

#### Ingested datasets (filecoin.data_portal.*)

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

#### Ingested datasets (filecoin.karma.*, filecoin.datacapstats.*)

Karma tables are refreshed by scheduled OSO ingestion jobs. For real-time data, use the Karma GAP API.

| Table | Description |
|-------|-------------|
| `filecoin.karma.registry` | Karma ProPGF project registry (~34 projects, links, metadata) |
| `filecoin.karma_milestones.milestones` | ProPGF grant milestones from Karma GAP API |
| `filecoin.datacapstats.verified_clients` | DataCapStats verified client records |
| `filecoin.datacapstats.verifiers` | DataCapStats allocator/verifier records |
| `filecoin.datacapstats.filplus_stats` | Network-level FilPlus statistics |

#### Static models

| Table | Description |
|-------|-------------|
| `filecoin.token_prices.token_prices` | Daily FIL/USD prices (Yahoo Finance + CoinGecko) |
| `filecoin.attribution_registry.artifact_registry` | Onchain artifact->entity mapping for onramp attribution |
| `filecoin.attribution_registry.client_sp_mapping` | Client->SP mappings from DataCapStats |
| `filecoin.onramp_dependency_scores.survey_submissions` | Dependency survey responses (0-5 importance scores) |

#### Staging: filecoin.staging_oso.* (OSO public data scoped to Filecoin)

| Table | Description |
|-------|-------------|
| `staging__oso__projects_by_collection` | Root of DAG — projects in `filecoin-*` collections |
| `staging__oso__projects` | Filecoin project metadata |
| `staging__oso__artifacts_by_project` | All artifact types per project |
| `staging__oso__repositories` | GitHub repo metadata (stars, forks, language, license) |
| `staging__oso__github_events` | GitHub events for tracked repos, >= 2024-01-01 |

#### Staging: filecoin.staging_external.* (external sources)

| Table | Description |
|-------|-------------|
| `staging__data_portal__allocators` | Allocator->client mapping with metadata |
| `staging__data_portal__clients` | Client snapshot stats |
| `staging__data_portal__client_providers` | Client->SP mapping |
| `staging__data_portal__daily_clients` | Deduplicated daily client metrics, >= 2024-01-01 |
| `staging__data_portal__daily_network` | Daily network-wide metrics, >= 2024-01-01 |
| `staging__data_portal__daily_sp_metrics` | Deduplicated daily SP metrics (~150 days only) |
| `staging__data_portal__filecoin_pay_operators` | Filecoin Pay operator staging |
| `staging__data_portal__filecoin_pay_rails` | Filecoin Pay rails staging |
| `staging__data_portal__warm_storage` | Warm storage staging |
| `staging__drips__rpgf_applications` | Drips RetroPGF records with JSON extraction |
| `staging__drips__rpgf_support_items` | Per-support-item funding: wei->FIL conversion |
| `staging__gsheets__onchain_artifacts` | Curated onchain artifact registry |
| `staging__gsheets__pod_membership` | Pod membership roster (FOC, LDO, Web2) |
| `staging__gsheets__public_grants` | Cleaned public grants with program mapping |
| `staging__gsheets__private_grants` | Cleaned private grants |
| `staging__karma__registry` | Karma ProPGF projects with flattened links |
| `staging__survey__submissions` | Dependency survey responses |
| `staging__survey__progress` | Survey completion progress |
| `staging__token_prices__fil_30d_avg` | 30-day rolling average FIL/USD price |

#### Entities: filecoin.entities.* (entity resolution)

| Table | Description |
|-------|-------------|
| `registry_ossd` | ~337 OSSD projects in Filecoin collections |
| `registry_propgf` | ~34 Karma ProPGF projects |
| `registry_retropgf` | ~111 Drips RetroPGF applications with earned amounts |
| `registry_data_portal` | ~523 active Data Portal entities |
| `bridge_karma_to_oso` | Karma slug -> OSSD project mapping |
| `bridge_drips_to_oso` | Drips repo -> OSSD mapping (override for renames) |
| `bridge_data_portal_to_oso` | Data Portal entity -> OSSD slug mapping |
| `projects_canonical` | Unified project list across all registries |
| `projects_bridged` | Cross-system identity mappings |
| `artifacts_github_repos` | GitHub repos per project |
| `artifacts_onchain` | Onchain artifacts (client IDs, SP IDs, allocator IDs, wallets) |
| `artifacts_grant_applications` | Grant applications per (project, program) |
| `dependency_classification` | Project type: pod, sp_operator, onramp, infrastructure, ecosystem_support |
| `dependency_matrix` | Weighted dependency edges from survey |

#### Events: filecoin.events.*

| Table | Description |
|-------|-------------|
| `events_github` | GitHub events for tracked repos |
| `events_onchain` | Daily client metrics joined to artifacts for entity resolution |
| `events_public_funding` | RetroPGF + ProPGF + Impact Grants + Hackathons |
| `events_private_funding` | Private grant events |

#### Metrics: filecoin.metrics.*

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
