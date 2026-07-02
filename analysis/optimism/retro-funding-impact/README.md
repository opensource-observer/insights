# Retro Funding Impact (local dashboard)

An interactive [marimo](https://marimo.io) dashboard that puts **funding** next to
**impact** for every Optimism Retro Funding recipient, from RetroPGF 2 through
Season 8. It runs **fully locally** from Parquet snapshots. No OSO API key or
network access required.

## What it shows

- **Program totals** across all recipients (79.5M OP / ~$171M, RF2 → S8).
- **Funding by round** (RetroPGF 2 through Season 8).
- **Funding leaderboard** of all 1,187 recipients, ranked by OP received.
- **Project explorer**: pick a project and one or more impact metrics (OP Mainnet
  and Superchain onchain activity, DefiLlama TVL/volume, GitHub dev activity) and
  read them against cumulative OP awarded on a shared timeline.

## Run it

From the repo root:

```bash
uv run marimo edit analysis/optimism/retro-funding-impact/retro-funding-impact.py
# or, app mode (read-only):
uv run marimo run analysis/optimism/retro-funding-impact/retro-funding-impact.py
```

Only needs `marimo`, `pandas`, `plotly`, and `pyarrow` (all in the repo's
`pyproject.toml`). The notebook reads the Parquet files in `./data` relative to
itself, so it works from any environment with those four packages.

## Files

| File | Rows | Description |
|---|---|---|
| `retro-funding-impact.py` | | The marimo notebook. |
| `data/rf_program_summary.parquet` | 1 | Program-wide totals (all recipients + mapped slice). |
| `data/rf_funding_by_round.parquet` | 7 | Funding totals per round (RF2 → S8). |
| `data/rf_funding_by_project.parquet` | 1,187 | Funding per recipient (OP + USD), `is_mapped` flag. |
| `data/rf_metrics_by_project_monthly.parquet` | ~226k | Monthly funding + impact metrics, long form, for mapped projects. |

## Data provenance

Snapshot exported **2026-07-02** from the OSO data warehouse
(`optimism.retro_funding_impact.*` models), which derive from:

- **Funding** — the [oss-funding](https://github.com/opensource-observer/oss-funding)
  registry, which records the native OP token amount and its USD value at the time
  of award, tagged by round. Totals reconcile to the canonical round allocations
  (RF2 10M OP, RF3 30M, RF4 10M, RF5 8M, RF6 2.4M, plus S7/S8 mission payouts).
- **Impact metrics** — OSO monthly timeseries (onchain activity on OP Mainnet and
  across the Superchain, DefiLlama, GitHub).

Impact metrics are available only for recipients mapped to an
[OSS Directory](https://github.com/opensource-observer/oss-directory) project
(692 of the 1,187 recipients). The rest (individuals, collections, events) are
counted in the funding totals but have no impact metrics.

**Not an ROI score.** Funding is shown alongside activity with no causal claim;
Retro Funding rewards work that has already happened.

The Season 7 and 8 measurement pipelines, eligibility checks, and reward
algorithms live in the Optimism Retro Funding repo:
[ethereum-optimism/Retro-Funding](https://github.com/ethereum-optimism/Retro-Funding).
This dashboard summarizes funding and impact outcomes across all rounds.

## Refreshing the snapshot

Re-export the four tables from the OSO warehouse (requires an `OSO_API_KEY` with
access to the `optimism` org) and overwrite the Parquet files in `./data`.
