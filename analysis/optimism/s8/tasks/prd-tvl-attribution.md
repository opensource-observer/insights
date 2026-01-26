# PRD: S8 TVL Attribution System

## Introduction

Create a deterministic system for assigning attribution percentages to S8 OP grants, representing the share of observed TVL impact reasonably attributable to each grant. The system produces a rounded percentage (100%, 50%, 20%, 10%, 5%, 2%, 1%) that is conservative by design, consistent across grants, fully deterministic given complete inputs, and robust to missing data.

This attribution percentage will be used by the Grants Council to evaluate program effectiveness and inform future funding decisions.

## Goals

- Assign a single rounded attribution percentage to each S8 TVL grant
- Produce a fully auditable CSV with all intermediate calculations
- Handle missing co-incentive data with conservative defaults
- Account for grant scope (targeted pools vs protocol-wide)
- Cap attribution based on grant size relative to baseline TVL
- Integrate with existing marimo notebook infrastructure

## User Stories

### US-001: Load and merge data sources
**Description:** As an analyst, I need to load grant data, TVL metrics, and co-incentive research into a unified dataframe so I can calculate attribution for each project.

**Acceptance Criteria:**
- [ ] Load grant metadata from pyoso (project, OP delivered, delivery date, chains, L2 address)
- [ ] Load TVL metrics from pyoso timeseries data
- [ ] Load co-incentive data from `S8 - Co-incentives Desk Research.csv`
- [ ] Load scope data from `S8 - Co-incentives GC Analysis.csv`
- [ ] Merge all sources on project name/slug with appropriate null handling
- [ ] Output merged dataframe with one row per project

### US-002: Calculate baseline and current TVL
**Description:** As an analyst, I need baseline TVL (at grant delivery) and current TVL for each project to measure the change.

**Acceptance Criteria:**
- [ ] Baseline TVL = 7-day average centered on delivery date
- [ ] Current TVL = 7-day average at most recent data point
- [ ] TVL scoped to chains specified in grant (from `chains` field)
- [ ] Handle projects with no TVL data gracefully (set to 0 or null with flag)
- [ ] Calculate `tvl_delta = current_tvl - baseline_tvl`

### US-003: Determine scope percentage for each project
**Description:** As an analyst, I need to determine what percentage of protocol-wide TVL change can be attributed to the grant scope (targeted pools vs global).

**Acceptance Criteria:**
- [ ] Parse "Scope" field from GC Analysis CSV to identify targeted pools/markets
- [ ] For projects with explicit pool lists, estimate scope percentage (e.g., 50% if targeting half of pools)
- [ ] For projects with "protocol-wide" scope, use 100%
- [ ] For projects with missing/unclear scope, use conservative default of 50%
- [ ] Store `scope_percentage` (0.0-1.0) and `scope_notes` (text explanation)

### US-004: Normalize OP grant to USD
**Description:** As an analyst, I need to convert OP token amounts to USD-equivalent for comparison with co-incentives.

**Acceptance Criteria:**
- [ ] Use fixed OP price of $0.35
- [ ] Calculate `op_usd = op_delivered * 0.35`
- [ ] Store both `op_delivered` and `op_usd` in output

### US-005: Extract and normalize co-incentive values
**Description:** As an analyst, I need to extract co-incentive USD values from the research data for each project.

**Acceptance Criteria:**
- [ ] Parse co-incentive descriptions from Desk Research CSV
- [ ] Extract explicit USD amounts where stated (e.g., "$1.125M", "$24,000")
- [ ] For token-denominated co-incentives (CAKE, EXTRA, TRUE, REZ), estimate USD value
- [ ] For "points program" or non-monetary co-incentives, assign conservative estimate or flag
- [ ] For "no mention" projects, use conservative default (assume co_usd = op_usd, i.e., 50% share)
- [ ] Store `co_incentive_usd`, `co_incentive_source`, and `co_incentive_notes`

### US-006: Calculate incentive share
**Description:** As an analyst, I need to calculate what share of total incentives came from the OP grant.

**Acceptance Criteria:**
- [ ] Calculate `incentive_share = op_usd / (op_usd + co_incentive_usd)`
- [ ] Handle edge case where both are 0 (set share to 0)
- [ ] Result is a decimal between 0.0 and 1.0
- [ ] Store `total_incentives_usd = op_usd + co_incentive_usd`

### US-007: Calculate attribution cap based on grant/TVL ratio
**Description:** As an analyst, I need to cap attribution based on how large the grant was relative to baseline TVL, using tiered buckets.

**Acceptance Criteria:**
- [ ] Calculate `grant_tvl_ratio = op_usd / baseline_tvl` (handle baseline_tvl = 0)
- [ ] Apply tiered cap logic:
  - `grant_tvl_ratio >= 50%` → `attribution_cap = 1.00` (100%)
  - `grant_tvl_ratio >= 20%` → `attribution_cap = 0.50` (50%)
  - `grant_tvl_ratio >= 10%` → `attribution_cap = 0.20` (20%)
  - `grant_tvl_ratio >= 5%` → `attribution_cap = 0.10` (10%)
  - `grant_tvl_ratio >= 2%` → `attribution_cap = 0.05` (5%)
  - `grant_tvl_ratio >= 1%` → `attribution_cap = 0.02` (2%)
  - `grant_tvl_ratio < 1%` → `attribution_cap = 0.01` (1%)
- [ ] For near-zero baseline TVL (< $10,000), allow 100% cap if grant was material
- [ ] Store `grant_tvl_ratio` and `attribution_cap`

### US-008: Compute final attribution percentage
**Description:** As an analyst, I need to combine scope, incentive share, and cap to produce the final attribution percentage.

**Acceptance Criteria:**
- [ ] Calculate raw attribution: `raw_attribution = scope_percentage * incentive_share`
- [ ] Apply cap: `capped_attribution = min(raw_attribution, attribution_cap)`
- [ ] Round to nearest allowed bucket: 100%, 50%, 20%, 10%, 5%, 2%, 1%
- [ ] Rounding logic: round to nearest bucket (e.g., 0.15 → 20%, 0.07 → 5%)
- [ ] Store `raw_attribution`, `capped_attribution`, and `final_attribution_pct`

### US-009: Generate output CSV with full audit trail
**Description:** As an analyst, I need a CSV with all inputs and intermediate calculations for transparency and review.

**Acceptance Criteria:**
- [ ] Output CSV includes columns:
  - `project_name`
  - `oso_project_slug`
  - `delivery_date`
  - `op_delivered`
  - `op_usd` (at $0.35)
  - `baseline_tvl`
  - `current_tvl`
  - `tvl_delta`
  - `scope_percentage`
  - `scope_notes`
  - `co_incentive_usd`
  - `co_incentive_source`
  - `co_incentive_notes`
  - `total_incentives_usd`
  - `incentive_share`
  - `grant_tvl_ratio`
  - `attribution_cap`
  - `raw_attribution`
  - `capped_attribution`
  - `final_attribution_pct`
  - `formula_applied` (text showing calculation)
- [ ] Save to `s8-tvl-attribution.csv` in the s8 directory
- [ ] Sort by project name alphabetically

### US-010: Add attribution to notebook display
**Description:** As an analyst, I want the attribution percentage displayed in the existing notebook's project deep dives.

**Acceptance Criteria:**
- [ ] Load attribution CSV in notebook
- [ ] Replace hardcoded "Attribution: 100%" with calculated value
- [ ] Show attribution percentage and brief formula in project cards
- [ ] Handle projects not in attribution CSV gracefully (show "N/A")

## Functional Requirements

- FR-1: Load grant metadata, TVL metrics, and co-incentive CSVs into unified dataframe
- FR-2: Calculate 7-day average baseline TVL centered on each project's delivery date
- FR-3: Calculate 7-day average current TVL from most recent data
- FR-4: Scope TVL to chains specified in grant metadata
- FR-5: Parse scope field to determine targeted vs protocol-wide coverage
- FR-6: Convert OP tokens to USD at fixed rate of $0.35
- FR-7: Extract or estimate co-incentive USD values from research data
- FR-8: Use conservative default (50% incentive share) when co-incentive data is missing
- FR-9: Calculate incentive share as `op_usd / (op_usd + co_incentive_usd)`
- FR-10: Calculate grant/TVL ratio for attribution cap determination
- FR-11: Apply tiered attribution cap based on grant/TVL ratio buckets
- FR-12: Compute final attribution as `min(scope_pct * incentive_share, cap)`
- FR-13: Round final attribution to nearest allowed bucket (1%, 2%, 5%, 10%, 20%, 50%, 100%)
- FR-14: Generate CSV with all intermediate calculations for auditability
- FR-15: Integrate attribution display into existing marimo notebook

## Non-Goals

- No automatic web scraping for co-incentive discovery (manual research already done)
- No dynamic OP price feeds (using fixed $0.35)
- No attribution for non-TVL metrics (transactions, users, etc.) in this iteration
- No historical attribution tracking (point-in-time calculation only)
- No automatic re-calculation on new data (manual refresh)

## Technical Considerations

- **Existing Infrastructure:** Build on `s8-strategic-insights.py` marimo notebook
- **Data Sources:**
  - pyoso: `optimism.grants.s8_tvl__projects`, `oso_community.karma.timeseries_metrics_by_project`
  - Local CSVs: `coincentives/S8 - Co-incentives Desk Research.csv`, `coincentives/S8 - Co-incentives GC Analysis.csv`
- **Dependencies:** pandas, pyoso, marimo
- **Output Location:** `/Users/cerv1/GitHub/insights/analysis/optimism/s8/s8-tvl-attribution.csv`

## Attribution Formula Summary

```
scope_percentage     = (targeted pools TVL / total protocol TVL) or manual estimate
incentive_share      = op_usd / (op_usd + co_incentive_usd)
grant_tvl_ratio      = op_usd / baseline_tvl
attribution_cap      = lookup_cap(grant_tvl_ratio)  # tiered buckets
raw_attribution      = scope_percentage * incentive_share
capped_attribution   = min(raw_attribution, attribution_cap)
final_attribution    = round_to_bucket(capped_attribution)  # 1%, 2%, 5%, 10%, 20%, 50%, 100%
```

## Tiered Attribution Cap Table

| Grant/TVL Ratio | Attribution Cap |
|-----------------|-----------------|
| ≥ 50%           | 100%            |
| ≥ 20%           | 50%             |
| ≥ 10%           | 20%             |
| ≥ 5%            | 10%             |
| ≥ 2%            | 5%              |
| ≥ 1%            | 2%              |
| < 1%            | 1%              |

## Success Metrics

- All 24 S8 TVL projects have a calculated attribution percentage
- CSV contains complete audit trail for each calculation
- Attribution percentages are defensible when reviewed by Grants Council
- Notebook displays attribution in project deep dives

## Open Questions

- Should there be a minimum TVL delta threshold below which attribution is 0%?
- For projects with negative TVL delta, should attribution still be calculated?
- Should the tiered cap boundaries be adjusted based on program feedback?
- How should "points program" co-incentives be valued (currently conservative estimate)?
