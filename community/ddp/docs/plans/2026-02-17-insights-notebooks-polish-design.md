# Insights Notebooks Polish — Design Document

**Date:** 2026-02-17
**Scope:** 5 active insight notebooks + Sidebar

## Goal

Get the five primary insight notebooks ready for a larger audience. Notebooks are consumed both via the DDP web app and as runnable marimo notebooks. Priority: cross-linking to metric definitions, public-facing polish, and SQL correctness.

## Decisions

| Decision | Choice |
|---|---|
| Audience | Both web app (rendered) and runnable locally |
| Cross-linking | Link to metric definitions; insights notebooks should not repeat what metric definitions explain |
| Speedrun style | Keep its distinct SRE palette — intentional for case study identity |
| Lifecycle framing | Title + accordion is sufficient; no executive framing block needed |
| developer-activity.py | Leave deprecated file as-is |

## Per-Notebook Audit

### 1. developer-report-2025.py

**Issues found:**
- `r"""` raw string in `header_title` cell (style guide: use `"""`)
- `test_connection` cell renders a visible status string to public users
- No link to the Activity metric definition
- No cross-links to related insights

**Changes:**
- Fix `r"""` → `"""` in `header_title`
- Hide `test_connection` output (keep cell, suppress output with no return)
- Add a "Related" footer linking to Activity metric definition + sibling insights

---

### 2. developer-lifecycle.py

**Issues found:**
- SQL queries `int_crypto_ecosystems_developer_lifecycle_monthly_aggregated` without schema prefix — verify if `oso.` prefix is needed
- `test_connection` cell renders visible status
- No link to Lifecycle metric definition
- `apply_ec_style` helper is duplicated (minor; not fixing helper duplication in this pass)
- No cross-links to related insights

**Changes:**
- Verify and fix schema prefix on lifecycle model query
- Hide `test_connection` output
- Add link to Lifecycle metric definition in the definitions accordion
- Add "Related" footer

---

### 3. developer-retention.py

**Issues found:**
- `test_connection` cell renders visible status
- No link to Retention metric definition
- Cross-ecosystem chart hardcodes "2023 cohort" in title — minor but worth flagging; this should update dynamically based on the cohort that has 2+ years of retention history
- `apply_ec_style` helper missing `tickformat` on xaxes (no time-based x-axis in this notebook, so not a bug)
- No cross-links to related insights

**Changes:**
- Hide `test_connection` output
- Add link to Retention metric definition in the definitions accordion
- Add "Related" footer

---

### 4. speedrun-ethereum.py

**Issues found:**
- Trailing empty cell at bottom (`@app.cell\ndef _():\n    return\n`)
- No cross-links to related insights
- Good otherwise — rich content, well-structured

**Changes:**
- Remove trailing empty cell
- Add "Related" footer after the Suggested Recommendations section

---

### 5. defi-developer-journeys.py

**Issues found (from first 100 lines; large file):**
- No cross-links to related insights (confirmed from structure)
- Good executive framing and structure otherwise

**Changes:**
- Add "Related" footer

---

### 6. Sidebar.tsx

**Issues found:**
- `retention.py` metric definition exists but is not in the Sidebar under Metric Definitions
- Metric Definitions section only has: Activity, Alignment, Lifecycle

**Changes:**
- Add `{ label: 'Retention', href: '/data/metric-definitions/retention' }` to Metric Definitions children

---

## "Related" Footer Pattern

Each insights notebook should end with a consistent `Related` cell:

```python
@app.cell(hide_code=True)
def related(mo):
    mo.md("""
    ## Related

    **Metric Definitions**
    - [Activity](../data/metric-definitions/activity.py) — Monthly Active Developer (MAD) methodology
    - [Lifecycle](../data/metric-definitions/lifecycle.py) — Developer stage definitions

    **Other Insights**
    - [2025 Developer Trends](./developer-report-2025.py)
    - [Lifecycle Analysis](./developer-lifecycle.py)
    - [Retention Analysis](./developer-retention.py)
    - [DeFi Developer Journeys](./defi-developer-journeys.py)
    - [Speedrun Ethereum](./speedrun-ethereum.py)
    """)
    return
```

Each notebook links to the relevant metric definitions for its topic, and lists all sibling insights (excluding itself).

---

## What We Are NOT Changing

- Speedrun's SRE color palette and chart helpers
- Developer-activity.py (deprecated, leave as-is)
- The `apply_ec_style` helper duplication (three notebooks each define it inline — not worth abstracting in this pass)
- Narrative/framing content in developer-lifecycle (title + accordion is sufficient)
- Overall structure of any notebook

---

## Metric Definitions Audit

Four notebooks under `data/metric-definitions/`. Two are well-developed; two are draft-level.

### activity.py — Good baseline

**Issues:**
- Most cells use anonymous `def _(mo)` naming instead of descriptive function names
- Missing Owner/Last Updated badge in title
- Related Models doesn't link to insights notebooks

**Changes:**
- Add title badge (Owner/Last Updated)
- Add cross-links to insights notebooks in Related Models

---

### lifecycle.py — Good baseline

**Issues:**
- Most cells use anonymous `def _(mo)` naming
- Missing Owner/Last Updated badge in title
- Related Models doesn't link to insights notebooks

**Changes:**
- Add title badge
- Add cross-link to Lifecycle Analysis insight in Related Models

---

### retention.py — Draft quality, needs significant work

**Issues:**
- `r"""` raw strings throughout (style guide violation)
- All SQL queries missing `oso.` schema prefix (users can't run them)
- No `apply_ec_style` helper, no EC color palette — charts use default plotly styling
- No live data exploration section (no stat widgets, no interactive charts at top)
- No Related Models section
- `__generated_with = "0.18.4"` (cosmetic)
- Charts hardcode Ethereum vs Solana / Jan 2023 cohort with no user controls

**Changes:**
- Fix `r"""` → `"""`
- Add `oso.` prefix to all SQL queries
- Add infrastructure cells at bottom: `apply_ec_style`, color constants, imports
- Add live data exploration section: ecosystem selector + stat widgets + retention curve chart (EC-styled)
- Fix chart styling to use EC palette and `apply_ec_style`
- Add Related Models section
- Add title badge

---

### alignment.py — Draft quality, needs significant work

**Issues:**
- `r"""` raw strings throughout
- All SQL queries missing `oso.` schema prefix
- No `apply_ec_style`, no EC color palette
- No live data exploration section
- No Related Models section
- `__generated_with = "0.18.4"` (cosmetic)
- Charts use default plotly styling
- Hardcoded date `2025-01-15` for all queries

**Changes:**
- Fix `r"""` → `"""`
- Add `oso.` prefix to all SQL queries
- Add infrastructure cells: `apply_ec_style`, color constants, imports
- Add live data exploration section: ecosystem selector + alignment distribution chart (EC-styled)
- Fix chart styling to use EC palette
- Add Related Models section
- Add title badge

---

## Implementation Order

1. Sidebar.tsx — add Retention metric definition link
2. activity.py — add title badge, add insights cross-links to Related Models
3. lifecycle.py — add title badge, add insights cross-links to Related Models
4. retention.py — major: fix r""", fix SQL prefixes, add EC infrastructure, add live section, add Related Models, add title badge
5. alignment.py — major: fix r""", fix SQL prefixes, add EC infrastructure, add live section, add Related Models, add title badge
6. developer-report-2025.py — fix `r"""`, hide test_connection, add Related footer
7. developer-lifecycle.py — verify schema prefix, hide test_connection, add Related footer
8. developer-retention.py — hide test_connection, add Related footer
9. speedrun-ethereum.py — remove empty cell, add Related footer
10. defi-developer-journeys.py — add Related footer
