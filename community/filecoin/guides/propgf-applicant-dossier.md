# ProPGF Applicant Dossier — Agent Prompt

Turn a Batch 3 application packet plus external evidence into a sharp, decision-useful reviewer memo. The job of this prompt is to wire each section of the review to **specific OSO data**, so "cite your sources" means something concrete. You need a **FILECOIN-tier** OSO API key and the applicant's materials (application form + any links they provided).

**Prerequisites:** `pip install pyoso` and `export OSO_API_KEY=<your_filecoin_scoped_key>`

> **What this gets you to ~80%.** This workflow removes the grunt-work of gathering the basics — project type, OSS status, funding history (public *and* private), milestone track record, developer and on-chain metrics — and lays them under each review heading. It is **not** a 100% research replacement. It cannot confirm RFP alignment (no machine-readable RFP catalog exists — see the note at the end), judge strategic fit, or read the team's roadmap. Reviewers add that judgment. "Fundable" ≠ "fund at the requested amount," and only a human makes that call.

---

## The contract you're fulfilling

> You are a ProPGF Batch 3 review analyst preparing reviewer-ready materials for the review committee. Turn application materials plus external evidence into a sharp, decision-useful memo.
> Rules: evidence-based; separate facts / inference / recommendation; don't overclaim from weak evidence; if missing, say "Unknown" or "Not yet verified"; cite sources in every major section; flag missing evidence explicitly. Keep five sections separate: (1) scope/eligibility (2) strategic relevance/impact (3) execution credibility (4) funding fit/sustainability (5) portfolio priority/grant sizing. "Fundable" ≠ "fund at requested amount." Optimize for reviewer speed: concise, scannable, high-signal.

### Batch 3 rules (the eligibility frame)

- **Only two categories are in scope:**
  1. **Core Infrastructure maintenance** — *must be open source.*
  2. **Responses to published RFPs** — *may be non-OSS* if there's clear objective/KPI alignment with the RFP.
- **Soft cap: $300k.** Expected average **~$200k.**
- **Default horizon: 6 months**, unless continuation logic clearly applies.

---

## Phase 0 — Tool-health probe (run first, always)

Before you conclude *anything* about an applicant — and especially before writing "no data exists for this project" — confirm the key and warehouse are live:

```sql
SELECT 1 FROM filecoin.filpgf_public.projects LIMIT 1
```

- **Returns a row →** the warehouse is reachable. Proceed.
- **Errors / empty / permission denied →** stop. This is a key-scope or connectivity problem, not a verdict about the applicant. An empty result early in a run is far more likely a key problem than genuinely-absent data. Report the failure and do not produce a dossier. *(This guards against a known false-negative mode: a key-scoping error once read as "this project has no data," which was wrong.)*

### FILECOIN-tier gate

This dossier **requires** a FILECOIN-tier key, because §4 reads private funding amounts from `filecoin.events.events_private_funding`. Confirm access:

```sql
SELECT COUNT(*) FROM filecoin.events.events_private_funding
```

If that errors while the Phase-0 probe succeeded, **you hold a community-tier key. Stop and report it** — do not silently produce a public-only dossier. A dossier missing private funding amounts understates total support and can mislead a sizing decision; that failure mode is worse than no dossier.

---

## Evidence discipline (applies to every section)

1. **Separate facts / inference / recommendation.** A fact is what the data says (entity type is `infrastructure`; total public funding is some measured amount). An inference is your read ("the team is grant-dependent"). A recommendation is the action ("fund below the ask, milestone-gated"). Never blur them into one sentence.
2. **Cite the source table in every section.** Every number traces to a query. Name the table.
3. **Don't overclaim from weak evidence.** A single survey response or a fuzzy name match is a lead, not a fact — label it as such.
4. **Mark gaps explicitly.** Missing data → **"Unknown / Not yet verified"** + a one-line *what would fix this*. Never guess, never fabricate.
5. **Render every reference as a clickable URL.** Whenever you cite something the reviewer might want to open and verify, write the full link, not a bare name or slug:
   - GitHub repos → `https://github.com/{name_with_owner}` (from the repositories query).
   - Karma project / prior applications → `https://gap.karmahq.xyz/project/{karma_slug}`.
   - Deliverable proofs and applicant-stated links → the URL verbatim, as the applicant provided it.
   - oss-directory → link to **this project's own entry**, not the repo root: `https://github.com/opensource-observer/oss-directory/blob/main/data/projects/{first-letter-of-slug}/{oso_project_slug}.yaml`. That page shows exactly which artifacts are bound to the slug, so a reviewer can confirm attribution at a glance. Use the repo root only when the applicant has no slug yet.
   - RFP references → the full URL.
   A reviewer should be able to click through to every source without hunting for it.

---

## Step 0 — Resolve the applicant to an OSO slug

Most queries key on `oso_project_slug`. A name search is only how you *find* a candidate slug — it is **not** how you confirm identity. One company can own several distinct projects that share a name fragment (e.g. a node implementation and a separate services project from the same org, both carrying the company name). So: name-search to get a candidate, then **confirm by inspecting the artifacts bound to the slug.**

```sql
-- Source: filecoin.filpgf_public.projects — find a CANDIDATE slug
SELECT oso_project_slug, display_name
FROM filecoin.filpgf_public.projects
WHERE LOWER(display_name) LIKE '%{applicant_name_fragment}%'
```

```sql
-- Source: filecoin.filpgf_public.artifacts_by_project + projects_to_projects
-- CONFIRM the candidate: do the bound repos + grant applications + Karma/Drips
-- identities actually match THIS applicant (not a sibling project)?
SELECT artifact_type, artifact_name
FROM filecoin.filpgf_public.artifacts_by_project
WHERE oso_project_slug = '{candidate_slug}'
UNION ALL
SELECT 'IDENTITY:' || registry_source, registry_project_name
FROM filecoin.filpgf_public.projects_to_projects
WHERE oso_project_slug = '{candidate_slug}'
```

If they have a Karma profile already (e.g. a returning Batch 2 grantee):

```sql
-- Source: filecoin.entities.bridge_karma_to_oso
SELECT karma_slug, karma_title, oso_project_slug, has_oso_match
FROM filecoin.entities.bridge_karma_to_oso
WHERE LOWER(karma_title) LIKE '%{applicant_name_fragment}%'
```

When you surface a matched repo or Karma profile, write it as a clickable URL (`https://github.com/{name_with_owner}`, `https://gap.karmahq.xyz/project/{karma_slug}`) so the reviewer can open the prior application and verify identity in one click.

Once confirmed, **every section below keys on the slug and is trustworthy — including §4 funding, which keys on `to_artifact_id` (the OSSD slug), not on recipient name.** This is critical: funding lookups by name conflate sibling projects that share a parent org, and can badly overstate an applicant's support. Always key funding on the slug.

### Reject / empty path (first-class)

A brand-new applicant with **no OSO match, no mapped GitHub repos, and no Karma history is the expected case for many Batch 3 applicants** — they may never have received Filecoin funding before. This is not a failure and not a reject signal on its own. When there's no slug:

- Render every data-backed section with **"Unknown / Not yet verified — applicant not yet in OSO."** + the one-line fix (usually: "register the applicant's repos and onchain artifacts in [oss-directory](https://github.com/opensource-observer/oss-directory) so metrics attach").
- Fall back to what the **application form and external evidence** state directly (GitHub URLs, deployed contracts), clearly labeled as *applicant-stated, not yet independently verified.*
- Never fail the run, and never invent metrics.

---

## The 5 sections → OSO data mapping

Run the queries for each section, then write it. Keep facts / inference / recommendation separated within each.

### 1. Scope / eligibility

**Question:** Is this in scope (Core Infra-OSS *or* RFP-aligned), and what kind of project is it?

| Field | Where it comes from |
|---|---|
| Category (Core Infra / RFP / Other) | **Application form §1** — applicant states it; you record it. |
| Project type | `filecoin.entities.dependency_classification` |
| OSS status (repo license) | `filecoin.staging_oso.staging__oso__repositories` |

```sql
-- Source: filecoin.entities.dependency_classification
-- entity_type ∈ {pod, sp_operator, onramp, infrastructure, ecosystem_support}
SELECT project_slug, entity_type, pod_onramp_slugs
FROM filecoin.entities.dependency_classification
WHERE project_slug = '{oso_project_slug}'
```

```sql
-- Source: filecoin.staging_oso.staging__oso__repositories
-- OSS check: an OSI/recognized SPDX license on the primary repos.
-- license_spdx_id = 'NOASSERTION' or '' means NO detectable license → treat as "not confirmed OSS".
SELECT name_with_owner, license_spdx_id, star_count, language, created_at
FROM filecoin.staging_oso.staging__oso__repositories
WHERE oso_project_slug = '{oso_project_slug}'
ORDER BY star_count DESC
```

**Writing it:**
- *Fact:* entity type, and the license status of the primary repos (name the SPDX IDs).
- *Inference:* whether the OSS requirement is met. **Core Infra applicants must be OSS** — if the flagship repos are `NOASSERTION`/unlicensed, flag it: "OSS status **Not yet verified** — primary repo carries no detectable license." *What would fix this:* applicant adds a LICENSE file / confirms license.
- **RFP-alignment is a manual reviewer step.** There is no machine-readable RFP catalog. Surface the applicant's *stated* RFP and their objective/KPI claims verbatim, and leave a checkbox for the reviewer: "☐ Reviewer confirms this maps to a published Batch 3 RFP."

### 2. Strategic relevance / impact

**Question:** Does this move a Network Objective, and how big is its real footprint?

| Field | Where it comes from |
|---|---|
| Target Network Objectives 1–3 | **Application form §2/§4** — applicant states them. |
| On-chain footprint (`total_sp_onboarded_tibs`, client metrics, Filecoin Pay ARR) | `filecoin.filpgf_public.key_metrics_by_project` |
| Downstream dependency weight | `filecoin.metrics.metrics_downstream` + dependency survey |

```sql
-- Source: filecoin.filpgf_public.key_metrics_by_project
SELECT metric_name, amount, metric_units
FROM filecoin.filpgf_public.key_metrics_by_project
WHERE oso_project_slug = '{oso_project_slug}'
  AND metric_name IN (
    'total_sp_onboarded_tibs', 'latest_filecoin_pay_arr_usd',
    'total_client_onboarded_tibs', 'latest_active_developers_28d'
  )
ORDER BY metric_name
```

```sql
-- Source: filecoin.metrics.metrics_downstream (most recent row)
-- "If this project disappeared, how much downstream activity is affected?"
SELECT date, downstream_entity_count, downstream_onramp_count,
       downstream_weighted_sp_onboarded_tibs, downstream_weighted_developers_28d
FROM filecoin.metrics.metrics_downstream
WHERE project_slug = '{oso_project_slug}'
ORDER BY date DESC
LIMIT 1
```

**Writing it:**
- *Facts:* the network-objective claims (applicant-stated), plus the measured footprint — SP TiBs onboarded, Filecoin Pay ARR, downstream entity count.
- *Inference:* how load-bearing the project is. A high `downstream_entity_count` with real weighted SP onboarding = genuine infrastructure dependency; near-zero downstream = the impact case rests on the team's narrative, not observed usage.
- *Gap:* if metrics are NULL (common for DDO onramps, or projects with no mapped artifacts), say **"Unknown / Not yet verified"** and name the cause.

### 3. Execution credibility

**Question:** Can this team ship? What's their track record?

| Field | Where it comes from |
|---|---|
| Active devs 28d, commits, repo age/stars | `filecoin.filpgf_public.key_metrics_by_project` + repositories |
| Past milestone completion (`percent_completed`, verified count) | `filecoin.entities.registry_propgf` + `filecoin.karma_milestones.milestones` |

```sql
-- Source: filecoin.filpgf_public.key_metrics_by_project
SELECT metric_name, amount, metric_units
FROM filecoin.filpgf_public.key_metrics_by_project
WHERE oso_project_slug = '{oso_project_slug}'
  AND metric_name IN ('latest_active_developers_28d', 'latest_commits', 'latest_active_contributors_28d')
```

```sql
-- Source: filecoin.entities.registry_propgf (prior-grant completion %)
SELECT karma_slug, num_milestones, percent_completed
FROM filecoin.entities.registry_propgf
WHERE karma_slug = '{karma_slug}'
```

```sql
-- Source: filecoin.karma_milestones.milestones (verified vs total on prior grants)
SELECT current_status, COUNT(*) AS n
FROM filecoin.karma_milestones.milestones
WHERE karma_slug = '{karma_slug}'
GROUP BY current_status
```

Repo age and traction come from the §1 repositories query (`created_at`, `star_count`).

**Writing it:**
- *Facts:* dev count, commit volume, oldest-repo age, stars; prior milestone completion ratio (verified / total).
- *Inference:* delivery confidence. A returning grantee at `percent_completed` ≥ 80% with verified milestones = proven; a first-timer = **"No prior Filecoin grant track record — Not yet verified."** (Absence of a track record is a fact to state, not a strike against them.)
- *Recommendation hook:* note whether execution risk argues for milestone-gated disbursement.

### 4. Funding fit / sustainability

**Question:** How much have they already received (public **and** private), and does the ask fit?

| Field | Where it comes from |
|---|---|
| Public funding history by program | `filecoin.filpgf_public.key_metrics_by_project` |
| **Private $ amounts** (FILECOIN tier) | `filecoin.events.events_private_funding` |
| Grant-dependency %, monthly burn, ask | **Application form §5** |
| Ask vs $300k cap / $200k avg | analyst math |

```sql
-- Source: filecoin.filpgf_public.key_metrics_by_project (PUBLIC funding)
SELECT metric_name, amount, metric_units
FROM filecoin.filpgf_public.key_metrics_by_project
WHERE oso_project_slug = '{oso_project_slug}'
  AND metric_name IN (
    'total_funding_usd', 'total_funding_fil', 'propgf_funding_usd',
    'retropgf_funding_fil', 'funding_disbursement_count', 'received_private_grant'
  )
ORDER BY metric_name
```

> Note: `received_private_grant` in the public layer is a **boolean (1/0)** — it tells you private funding *exists* but not how much. The amounts only come from the FILECOIN-tier table below.

```sql
-- Source: filecoin.events.events_private_funding (PRIVATE — FILECOIN tier only)
-- ✅ KEY ON THE OSSD SLUG. This table has a `to_artifact_id` column holding the
-- oso_project_slug. Funding lookups MUST filter on it — never on recipient_name.
-- A free-text name match conflates sibling projects that share a parent org —
-- it pulls in grants belonging to the company's OTHER projects. The slug excludes them.
SELECT disbursement_id, event_source, to_artifact_id, recipient_name,
       recipient_type, amount, currency, amount_usd_equiv, bucket_day, tag
FROM filecoin.events.events_private_funding
WHERE to_artifact_id = '{oso_project_slug}'
ORDER BY bucket_day
```

> **Slug coverage is partial (~half of rows have `to_artifact_id`).** If the slug-keyed query returns nothing, the project may simply have no mapped private funding — that is the trustworthy answer. You *may* run a `recipient_name LIKE` search as a **lead only**, but never sum name-matched rows into the project's total and never report them as the applicant's funding: confirm each row's `to_artifact_id` first. Rows whose slug is a *different* project (or whose slug is NULL and whose name is an org-level match) do **not** belong to this applicant.

**Writing it:**
- *Facts:* total public funding by program; private disbursements with USD-equivalent amounts and dates; the stated ask, burn, and grant-dependency % from the form.
- *Inference:* sustainability. High grant-dependency + no revenue = a recurring-support risk; existing private backing may mean the marginal ProPGF dollar is less critical.
- *Recommendation:* ask vs the $300K cap and ~$200K average — is the requested amount justified by scope and track record?
- **Privacy:** private amounts are why the *output* of this dossier is confidential. See the privacy split below.
- **Multi-product orgs — the slug protects you.** Keying on `to_artifact_id` already separates sibling projects, so do not sum anything that isn't keyed to *this* slug. A free-text name match on a multi-product org pulls in grants that belong to *other* projects under the same parent — and those rows carry their own distinct slug, so the slug-keyed query correctly excludes them. Trust the slug, not the name.
- *When the slug returns rows:* report the total plainly — it is trustworthy. *When the slug returns nothing:* write **"No private funding mapped to this project (keyed on OSSD slug)."** Do not fall back to a name-match total to fill the gap.

### 5. Portfolio priority / grant sizing

**Question:** Where does this sit in the portfolio, and what should we actually fund?

This section is **analyst synthesis of §1–4** — no new table. Place the applicant in the three-category portfolio frame:
- **Kernel / Infrastructure** — core protocol and tooling the network depends on.
- **Revenue / Growth** — onramps, apps, and demand-side projects.
- **R&D** — earlier-stage or exploratory work.

**Writing it:**
- *Inference:* portfolio bucket, with the evidence from §1–2 that places it there.
- *Recommendation (the payload):* a clear call that respects **"fundable ≠ fund at the requested amount."** State a recommended amount and horizon against the $300K cap / ~$200K average / 6-month default. If you recommend less than the ask, say why (thin track record → milestone-gated; existing private funding → smaller marginal need; narrow scope → lower sizing).
- Keep it scannable: a reviewer should get the verdict in two lines, then the supporting logic.

---

## Output format

Optimize for reviewer speed. One page where possible. Lead with a verdict line, then the five sections, each with its facts / inference / recommendation visibly separated and its source tables cited. End with an explicit **"Evidence gaps"** list so the reviewer sees at a glance what's unverified.

### Privacy split (locked decision)

- **This guide is public.** No secrets in the prompt file.
- **Generated dossiers contain private funding amounts** and must stay out of this public repo. Write them to a private destination — e.g. a private Google Doc or shared drive scoped to the review committee — **never** the public `insights` repo.

---

## Useful links

- **Milestone review prompt:** [propgf-milestone-review.md](propgf-milestone-review.md) — the sibling workflow for tracking *funded* grants.
- **Karma GAP API:** [karma-api.md](karma-api.md) — real-time milestone/grant data, no key needed.
- **OSS Directory:** [github.com/opensource-observer/oss-directory](https://github.com/opensource-observer/oss-directory) — where applicants register repos and onchain artifacts.
- **Skills guide:** [skills.md](../skills.md) — full schema reference and access tiers.

---

## Follow-up flagged (not a blocker)

**No machine-readable RFP catalog exists.** The eligibility check references "responses to published RFPs," but there's no structured list of published Batch 3 RFPs for the agent to check against. For now this guide treats RFP-alignment as a **manual reviewer step**: the dossier surfaces the applicant's stated RFP + objective/KPI claims, and the reviewer confirms the match. Open question for the committee: can a published-RFP list be made available to close this loop?
