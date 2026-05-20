# ProPGF Grant Monitoring Report — Agent Prompt

Generate a monthly monitoring report for a Filecoin ProPGF grant recipient. You need a Filecoin-scoped OSO API key and a Karma slug.

**Prerequisites:** `pip install pyoso` and `export OSO_API_KEY=<your_filecoin_scoped_key>`

---

## Step 1: Identify the project and available data

Start with the Karma slug. If you only have a project name, find it:

```sql
SELECT karma_slug, karma_title, karma_description, num_milestones, percent_completed
FROM filecoin.entities.registry_propgf
ORDER BY karma_title
```

Then check what data sources exist for this project:

```sql
-- Does this project have an OSO match? (GitHub repos, funding events, etc.)
SELECT karma_slug, karma_title, oso_project_slug, has_oso_match
FROM filecoin.entities.bridge_karma_to_oso
WHERE karma_slug = '{karma_slug}'
```

```sql
-- Is this a pod grant? If so, metrics live at the pod level.
SELECT pod_slug, pod_display_name, member_slug, member_role, criticality
FROM filecoin.staging_external.staging__gsheets__pod_membership
WHERE pod_slug IN ('foc', 'ldo', 'web2')
ORDER BY pod_slug, criticality, member_slug
```

**Pod grants** map Karma slugs to pod slugs: `foc-filecoin-onachain-cloud` → `foc`, `large-data-onboarding-pod-ldo-pod` → `ldo`, `web2-object-storage-pod` → `web2`.

---

## Step 2: Pull milestones

```sql
SELECT
  milestone_title,
  milestone_description,
  ends_at,
  current_status,
  status_updated_at,
  status_reason,
  deliverable_proofs
FROM filecoin.karma_milestones.milestones
WHERE karma_slug = '{karma_slug}'
ORDER BY ends_at
```

**Determine status for each milestone:**

| Karma `current_status` | Due date vs today | Report as |
|---|---|---|
| `verified` | any | **Verified** |
| `completed` | any | **Submitted** (awaiting verification) |
| other | past due | **Overdue** |
| other | within 30 days | **At Risk** |
| other | more than 30 days out | **Pending** |

**Overall grant status:** 2+ overdue → Behind; 1 overdue or any at risk → Needs Review; otherwise → On Track.

---

## Step 3: Discover the right metrics

This is the most important step. Don't just grab everything — choose metrics that are relevant to what the grant is supposed to achieve.

### 3a. Read the grant scope

Look at `milestone_description` from Step 2. What does the project promise?
- Building DeFi infrastructure? → Look for TVL, on-chain metrics, contract interactions
- Developing tools/SDKs? → Look for GitHub activity, releases, downstream usage
- Running storage infrastructure? → Look for SP metrics, data onboarded, block rewards
- Growing adoption? → Look for user counts, Filecoin Pay ARR, unique payers

### 3b. See what metrics actually exist

**For projects with `has_oso_match = true`:**

```sql
-- What snapshot metrics exist for this project?
SELECT metric_name, metric_display_name, metric_units, amount
FROM filecoin.filpgf_public.key_metrics_by_project
WHERE oso_project_slug = '{oso_project_slug}'
ORDER BY metric_name
```

```sql
-- What time series are available?
SELECT DISTINCT metric_name, metric_display_name, metric_units, time_interval,
       MIN(sample_date) AS first_date, MAX(sample_date) AS last_date
FROM filecoin.filpgf_public.timeseries_metrics_by_project
WHERE oso_project_slug = '{oso_project_slug}'
GROUP BY 1, 2, 3, 4
ORDER BY metric_name
```

**For pod grants:**

```sql
-- Pod-level snapshot metrics
SELECT metric_name, metric_display_name, metric_units,
       member_count, sum_amount, avg_amount
FROM filecoin.filpgf_public.key_metrics_by_pod
WHERE pod_slug = '{pod_slug}'
ORDER BY metric_name
```

```sql
-- Pod-level time series
SELECT DISTINCT metric_name, metric_display_name, metric_units, time_interval,
       MIN(sample_date) AS first_date, MAX(sample_date) AS last_date
FROM filecoin.filpgf_public.timeseries_metrics_by_pod
WHERE pod_slug = '{pod_slug}'
GROUP BY 1, 2, 3, 4
ORDER BY metric_name
```

**For all projects — check the metric catalog:**

```sql
SELECT metric_name, metric_display_name, metric_units, metric_description, metric_category
FROM filecoin.filpgf_public.metric_catalog
ORDER BY metric_category, metric_name
```

### 3c. Choose 3-5 headline metrics

Pick metrics that:
1. **Directly relate to the grant's stated goals** — if they promised TVL growth, show TVL
2. **Are available with reasonable coverage** — check `member_count` for pods, or whether the time series has data in the grant period
3. **Show change over time** — a metric that's flat since before the grant tells a different story than one trending up
4. **Include at least one development metric and one impact metric** — developer activity shows work is happening; on-chain/usage metrics show the work is landing

### 3d. Pull the time series for your chosen metrics

Limit to 3 months before grant start for context, not the full history:

```sql
SELECT sample_date, metric_name, amount
FROM filecoin.filpgf_public.timeseries_metrics_by_project
WHERE oso_project_slug = '{oso_project_slug}'
  AND metric_name IN ('commits', 'active_developers_28d', '{other_relevant_metric}')
  AND time_interval = 'monthly'
  AND sample_date >= DATE '{3_months_before_grant_start}'
ORDER BY sample_date
```

---

## Step 4: Write the report

Structure the report in four sections:

### 01 / Executive Summary

- **Grant scope:** One paragraph on what the project received and what they're building
- **Key numbers:** Milestones completed vs total, months elapsed vs total, next milestone due date
- **Status:** On Track / Needs Review / Behind (derived from milestone math, not opinion)
- **2-3 sentences** covering: what happened this month, where things stand, what needs attention

### 02 / Milestone Progress

For each milestone:
- Title, due date, and status (Verified/Submitted/Overdue/At Risk/Pending)
- For **Verified**: summarize the `status_reason` and link to evidence from `deliverable_proofs`
- For **Overdue**: state the due date and that no completion has been submitted
- For **Pending/At Risk**: note what's expected and when

Close with 1-2 sentences interpreting overall progress.

### 03 / Metrics Analysis

- **KPI headline:** 3-5 key numbers that summarize the project's observable footprint
- **Charts:** Time series of chosen metrics, anchored to the grant start date. Include a vertical marker at grant start so the reader can see before vs after.
- **Interpretation:** For each chart, one sentence on what it means — not what it shows. "Developer activity remains steady at ~99 active developers" not "The chart shows 99 developers."
- **Data coverage note:** Be honest about what you can and can't see. Name the data source, what it covers, and what's missing. For pod grants: "Pod metrics aggregate across N member projects — they reflect the pod's collective footprint, not {project}-specific usage."
- **Interactive exploration:** If generating an interactive notebook, include a dropdown that lets the reviewer explore any available metric over the same time window.

### 04 / Next Steps

A checklist of action items for the reviewer. Tag each item:
- **Verification** — milestones needing completion evidence
- **Artifact Request** — missing repos, contracts, or addresses that should be mapped in [oss-directory](https://github.com/opensource-observer/oss-directory) to enable tracking
- **Data Gap** — metrics that can't be tracked yet and what would fix it
- **Follow-up** — questions or clarifications to raise with the project team

Each item should be specific enough to copy into a follow-up email or Karma comment.

---

## Editorial guidelines

**Professional neutral.** The audience is grant reviewers, but expect the project team will see this too.

- State what's verified and link to evidence. State what's overdue without editorializing.
- Every claim should include a number, a date, or a source.
- Be honest about data gaps — "No quantitative metrics available; FOC does not have mapped repositories in OSO" is better than silence.
- Interpret, don't describe. "USDFC TVL declined 15% since grant start, from $480K to $380K" — not "The chart shows TVL over time."
- Don't cheerleard and don't alarm. Let the data speak.

---

## Useful links

- **Karma GAP:** `https://gap.karmahq.xyz/project/{karma_slug}` — the project's milestone page
- **OSO Dashboard:** [oso.xyz/filecoin/Public-Goods-Funding](https://www.oso.xyz/filecoin/Public-Goods-Funding)
- **OSS Directory:** [github.com/opensource-observer/oss-directory](https://github.com/opensource-observer/oss-directory) — where project artifacts (repos, contracts) are registered
- **Skills guide:** See `skills.md` in this directory for the full schema reference and starter queries
