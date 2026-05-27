# ProPGF Milestone Review — Agent Prompt

Generate a monthly milestone-review report for a Filecoin ProPGF grant recipient: track a funded project against its committed milestones and surface the observable footprint behind them. You need a Filecoin-scoped OSO API key and a Karma slug.

**Prerequisites:** `pip install pyoso` and `export OSO_API_KEY=<your_filecoin_scoped_key>`

> **What this gets you to ~80%.** This workflow removes the grunt-work of gathering the basics — milestone status, the metrics behind them, project type, funding context — and assembles them into a reviewer-ready report. It is **not** a 100% research replacement. It does not read the grantee's Slack, judge whether a "verified" milestone was verified rigorously, or weigh strategic fit. Reviewers add that judgment. Treat the output as a strong first draft.

---

## Phase 0 — Tool-health probe (run first, always)

Before you conclude *anything* about a project — and especially before writing "no data exists" — confirm the key and warehouse are live:

```sql
SELECT 1 FROM filecoin.filpgf_public.projects LIMIT 1
```

- **Returns a row →** the warehouse is reachable and your key has at least COMMUNITY scope. Proceed.
- **Errors / empty / permission denied →** stop. This is a key-scope or connectivity problem, not a verdict about the project. Report the failure and do not produce a report. An empty project result early in a run is far more likely a key problem than genuinely-absent data.

This guide assumes a **FILECOIN-tier** key (it reads `filecoin.karma_milestones.*` and `filecoin.entities.*`). If those tables error but `filpgf_public` works, you have a community-tier key — stop and report that, rather than silently producing a thinner report.

---

## Evidence discipline (applies to every section)

This report will be read by grant reviewers, and the project team will likely see it too. Hold to these rules throughout:

1. **Separate facts from inference from recommendation.** A fact is something the data says (a milestone is `verified`; commits fell from 157 to 26). An inference is your read of it ("development has slowed since the grant period opened"). A recommendation is what you'd do about it ("request a status update on M2 before the next disbursement"). Never let them blur into one sentence.
2. **Cite the source table in every section.** Every number traces to a query. Name the table — `filecoin.karma_milestones.milestones`, `filecoin.filpgf_public.key_metrics_by_project` — so a reviewer can re-run it.
3. **Mark gaps explicitly.** When data is missing, write **"Unknown / Not yet verified"** and a one-line *what would fix this* — never guess, never paper over the gap, never fabricate.
4. **Every claim carries a number, a date, or a source.** No adjective stands alone.

---

## Step 1: Identify the project and available data

Start with the Karma slug. If you only have a project name, find it:

```sql
-- Source: filecoin.entities.registry_propgf
SELECT karma_slug, karma_title, karma_description, num_milestones, percent_completed
FROM filecoin.entities.registry_propgf
ORDER BY karma_title
```

Then check what data sources exist for this project:

```sql
-- Source: filecoin.entities.bridge_karma_to_oso
-- Does this project have an OSO match? (GitHub repos, funding events, etc.)
SELECT karma_slug, karma_title, oso_project_slug, has_oso_match
FROM filecoin.entities.bridge_karma_to_oso
WHERE karma_slug = '{karma_slug}'
```

```sql
-- Source: filecoin.staging_external.staging__gsheets__pod_membership
-- Is this a pod grant? If so, metrics live at the pod level.
SELECT pod_slug, pod_display_name, member_slug, member_role, criticality
FROM filecoin.staging_external.staging__gsheets__pod_membership
WHERE pod_slug IN ('foc', 'ldo', 'web2')
ORDER BY pod_slug, criticality, member_slug
```

**Pod grants** map Karma slugs to pod slugs: `foc-filecoin-onachain-cloud` → `foc`, `large-data-onboarding-pod-ldo-pod` → `ldo`, `web2-object-storage-pod` → `web2`.

### Reject / empty path (first-class)

A project with no OSO match, no GitHub repos, or no Karma profile is a **valid outcome**, not a failure. Render the report anyway:

- `has_oso_match = false` → metrics sections say **"Unknown / Not yet verified — no OSO project match."** *What would fix this:* register the project's repos and onchain artifacts in [oss-directory](https://github.com/opensource-observer/oss-directory).
- No Karma milestones returned → milestone section says **"Unknown / Not yet verified — no milestones found on Karma for `{karma_slug}`."** *What would fix this:* confirm the grantee has created their Karma project and attached milestones.

Never fail the run and never invent milestones or metrics to fill the gap.

---

## Step 2: Pull milestones

```sql
-- Source: filecoin.karma_milestones.milestones
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

For real-time freshness (e.g. a milestone submitted in the last few hours), hit the Karma GAP API instead — see [karma-api.md](karma-api.md). The warehouse table lags the live API by hours to days.

**Determine status for each milestone (fact, from the data):**

| Karma `current_status` | Due date vs today | Report as |
|---|---|---|
| `verified` | any | **Verified** |
| `completed` | any | **Submitted** (awaiting verification) |
| other | past due | **Overdue** |
| other | within 30 days | **At Risk** |
| other | more than 30 days out | **Pending** |

**Overall grant status (fact, derived — not opinion):** 2+ overdue → Behind; 1 overdue or any at risk → Needs Review; otherwise → On Track.

---

## Step 3: Discover the right metrics

This is the most important step. Don't just grab everything — choose metrics relevant to what the grant is supposed to achieve.

### 3a. Read the grant scope

Look at `milestone_description` from Step 2. What does the project promise?
- Building DeFi infrastructure? → TVL, on-chain metrics, contract interactions
- Developing tools/SDKs? → GitHub activity, releases, downstream usage
- Running storage infrastructure? → SP metrics, data onboarded, block rewards
- Growing adoption? → user counts, Filecoin Pay ARR, unique payers

### 3b. See what metrics actually exist

**For projects with `has_oso_match = true`:**

```sql
-- Source: filecoin.filpgf_public.key_metrics_by_project
SELECT metric_name, metric_display_name, metric_units, amount
FROM filecoin.filpgf_public.key_metrics_by_project
WHERE oso_project_slug = '{oso_project_slug}'
ORDER BY metric_name
```

```sql
-- Source: filecoin.filpgf_public.timeseries_metrics_by_project
SELECT DISTINCT metric_name, metric_display_name, metric_units, time_interval,
       MIN(sample_date) AS first_date, MAX(sample_date) AS last_date
FROM filecoin.filpgf_public.timeseries_metrics_by_project
WHERE oso_project_slug = '{oso_project_slug}'
GROUP BY 1, 2, 3, 4
ORDER BY metric_name
```

**For pod grants:**

```sql
-- Source: filecoin.filpgf_public.key_metrics_by_pod
SELECT metric_name, metric_display_name, metric_units,
       member_count, sum_amount, avg_amount
FROM filecoin.filpgf_public.key_metrics_by_pod
WHERE pod_slug = '{pod_slug}'
ORDER BY metric_name
```

```sql
-- Source: filecoin.filpgf_public.timeseries_metrics_by_pod
SELECT DISTINCT metric_name, metric_display_name, metric_units, time_interval,
       MIN(sample_date) AS first_date, MAX(sample_date) AS last_date
FROM filecoin.filpgf_public.timeseries_metrics_by_pod
WHERE pod_slug = '{pod_slug}'
GROUP BY 1, 2, 3, 4
ORDER BY metric_name
```

**For all projects — check the metric catalog:**

```sql
-- Source: filecoin.filpgf_public.metric_catalog
SELECT metric_name, metric_display_name, metric_units, metric_description, metric_category
FROM filecoin.filpgf_public.metric_catalog
ORDER BY metric_category, metric_name
```

### 3c. Choose 3-5 headline metrics

Pick metrics that:
1. **Directly relate to the grant's stated goals** — if they promised TVL growth, show TVL.
2. **Are available with reasonable coverage** — check `member_count` for pods, or whether the time series has data in the grant period.
3. **Show change over time** — a metric flat since before the grant tells a different story than one trending up.
4. **Include at least one development metric and one impact metric** — dev activity shows work is happening; on-chain/usage metrics show it's landing.

### 3d. Pull the time series for your chosen metrics

Limit to ~3 months before grant start for context, not full history:

```sql
-- Source: filecoin.filpgf_public.timeseries_metrics_by_project
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

Four sections. Within each, keep **facts** (what the data says), **inference** (your read), and **recommendation** (what to do) visibly separate — a short labeled line, a sub-bullet, or distinct sentences. Cite the source table for every number.

### 01 / Executive Summary

- **Grant scope:** One paragraph on what the project received and what they're building. *(Source: `registry_propgf`, milestone descriptions.)*
- **Key numbers (facts):** Milestones completed vs total, months elapsed vs total, next milestone due date.
- **Status (fact, derived):** On Track / Needs Review / Behind — from the milestone math, not opinion.
- **2-3 sentences (inference):** what happened this period, where things stand, what needs attention.

### 02 / Milestone Progress

For each milestone (facts first):
- Title, due date, and status (Verified/Submitted/Overdue/At Risk/Pending). *(Source: `filecoin.karma_milestones.milestones`.)*
- For **Verified**: summarize the `status_reason` and link to evidence from `deliverable_proofs`.
- For **Overdue**: state the due date and that no completion has been submitted.
- For **Pending/At Risk**: note what's expected and when.

Close with 1-2 sentences (inference) interpreting overall progress. If a milestone is verified but the linked proof is unreachable or thin, say so: **"Marked verified on Karma; proof link not independently checked — Not yet verified by this review."**

### 03 / Metrics Analysis

- **KPI headline (facts):** 3-5 key numbers summarizing the project's observable footprint, each with its source table.
- **Charts:** Time series of chosen metrics, anchored to the grant start date with a vertical marker so the reader sees before vs after.
- **Interpretation (inference):** For each chart, one sentence on what it *means* — not what it *shows*. "Developer activity remains steady at ~99 active developers," not "the chart shows 99 developers."
- **Data coverage note (facts + gaps):** Name the source, what it covers, and what's missing. Mark unmeasurable things **"Unknown / Not yet verified"** with a one-line fix. For pod grants: "Pod metrics aggregate across N member projects — they reflect the pod's collective footprint, not `{project}`-specific usage."

### 04 / Next Steps

A checklist of action items (recommendations) for the reviewer. Tag each:
- **Verification** — milestones needing completion evidence.
- **Artifact Request** — missing repos, contracts, or addresses to map in [oss-directory](https://github.com/opensource-observer/oss-directory) to enable tracking.
- **Data Gap** — metrics that can't be tracked yet and what would fix it.
- **Follow-up** — questions or clarifications to raise with the project team.

Each item should be specific enough to copy into a follow-up email or Karma comment.

---

## Editorial guidelines

**Professional neutral.** The audience is grant reviewers, but expect the project team will see this too.

- State what's verified and link to evidence. State what's overdue without editorializing.
- Every claim includes a number, a date, or a source.
- Be honest about data gaps — "No quantitative metrics available; FOC does not have mapped repositories in OSO" beats silence.
- Interpret, don't describe. "USDFC TVL declined 15% since grant start, from $480K to $380K" — not "the chart shows TVL over time."
- Don't cheerlead and don't alarm. Let the data speak.

---

## Output exemplar (sanitized excerpt)

The format below is from the worked example run against `secured-finance` (a real Batch 2 recipient). The full output is kept privately (a Google Doc shared with the review committee); numbers here are real but the section is trimmed for illustration, and it carries no private funding amounts.

> **01 / Executive Summary**
> **Status: Needs Review** (1 overdue, 1 at risk — derived from milestone math).
> *Facts:* 1 of 3 milestones verified. ProPGF grant of $225K *(Source: `key_metrics_by_project`, `propgf_funding_usd`)*. Next milestone ("FVM Yield Infrastructure") due 2026-05-31.
> *Inference:* M1 (UI v2) shipped and was verified on 2026-04-20; the two Yield Infrastructure milestones remain `pending` with one already past its 2026-04-30 due date.
> *Recommendation:* request a status update on the Yield Infrastructure track before the next disbursement.
>
> **03 / Metrics Analysis (excerpt)**
> *Fact:* Monthly commits fell from 157 (Nov 2025) to 26 (May 2026); active developers 28d held between 4 and 13 over the same window *(Source: `timeseries_metrics_by_project`)*.
> *Inference:* Engineering throughput has cooled since late 2025, consistent with a shift from feature build-out to maintenance.
> *Gap:* On-chain USDFC TVL is **Unknown / Not yet verified** — no TVL metric is mapped for this project. *What would fix this:* register the USDFC contracts in oss-directory so on-chain metrics attach.

---

## Useful links

- **Karma GAP:** `https://gap.karmahq.xyz/project/{karma_slug}` — the project's milestone page
- **OSO Dashboard:** [oso.xyz/filecoin/Public-Goods-Funding](https://www.oso.xyz/filecoin/Public-Goods-Funding)
- **OSS Directory:** [github.com/opensource-observer/oss-directory](https://github.com/opensource-observer/oss-directory) — where project artifacts (repos, contracts) are registered
- **Applicant dossier prompt:** [propgf-applicant-dossier.md](propgf-applicant-dossier.md) — the sibling workflow for evaluating *new* applications
- **Skills guide:** [skills.md](../skills.md) — full schema reference and starter queries
