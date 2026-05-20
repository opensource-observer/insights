"""Pull Pro PGF metrics and rebuild the metric selection form.

Discovers Pro PGF projects from filecoin.filpgf_public.* mart models,
queries their timeseries metrics, backfills downstream entity counts,
and updates the embedded JSON in the HTML form.

Only queries filpgf_public.* models — no upstream/staging access needed.
Grant names, batches, and entity types are maintained as static config
below (they reflect governance decisions, not derived data).

Usage:
    pip install pyoso
    export OSO_API_KEY=<your_filecoin_scoped_key>
    python select_propgf_metrics.py
"""
import json
import re
from pathlib import Path

from pyoso import Client

client = Client()

HTML_FILE = Path(__file__).parent.parent / "examples" / "propgf-metric-selection.html"

# --- Static config: grants and entity types ---
# These are governance artifacts maintained manually.
# Update when new batches are approved or entity classifications change.

GRANTS = [
    # Batch 1 (Sep-Dec 2025)
    {"grant_name": "IPNI", "batch": "Batch1", "oso_project_slug": "ipni", "total_amount": 280000},
    {"grant_name": "Curio Storage", "batch": "Batch1", "oso_project_slug": "curio-filecoin-project", "total_amount": 561300},
    {"grant_name": "Filecoin EconoLens MCP Server", "batch": "Batch1", "oso_project_slug": "celtd", "total_amount": 60000},
    {"grant_name": "Game Theoretic Programmable Fil+ Allocator", "batch": "Batch1", "oso_project_slug": "celtd", "total_amount": 80000},
    {"grant_name": "chainfee", "batch": "Batch1", "oso_project_slug": "chainfee-beck-8", "total_amount": 25000},
    {"grant_name": "(FilCDN) Filecoin Retrieval Checkers as FWS Services", "batch": "Batch1", "oso_project_slug": None, "total_amount": 333334},
    {"grant_name": "Fil Note", "batch": "Batch1", "oso_project_slug": "filnote", "total_amount": 100000},
    {"grant_name": "Filecoin Developer Tooling (FIL-B)", "batch": "Batch1", "oso_project_slug": "fil-builders", "total_amount": 200000},
    {"grant_name": "FIL Ponto", "batch": "Batch1", "oso_project_slug": "filponto", "total_amount": 500000},
    {"grant_name": "Lynx", "batch": "Batch1", "oso_project_slug": "lynx-26dos", "total_amount": 80000},
    {"grant_name": "Titan Network (SP Bandwidth)", "batch": "Batch1", "oso_project_slug": "titannet-dao", "total_amount": 50000},
    {"grant_name": "EverMedia Vault", "batch": "Batch1", "oso_project_slug": "evermediavault", "total_amount": 40000},
    {"grant_name": "CIDgravity gateway", "batch": "Batch1", "oso_project_slug": "cidgravity", "total_amount": 50000},
    # Batch 2 (Feb 2026)
    {"grant_name": "Calib Miner", "batch": "Batch2", "oso_project_slug": None, "total_amount": 28000},
    {"grant_name": "Curio Storage", "batch": "Batch2", "oso_project_slug": "curio-filecoin-project", "total_amount": 500000},
    {"grant_name": "Drand", "batch": "Batch2", "oso_project_slug": "drand", "total_amount": 120000},
    {"grant_name": "FF Infra & Coordination Stewardship", "batch": "Batch2", "oso_project_slug": None, "total_amount": 101200},
    {"grant_name": "FIL-B", "batch": "Batch2", "oso_project_slug": "fil-builders", "total_amount": 420000},
    {"grant_name": "FilPonto", "batch": "Batch2", "oso_project_slug": "filponto", "total_amount": 300000},
    {"grant_name": "Filecoin Infrastructure Services", "batch": "Batch2", "oso_project_slug": None, "total_amount": 138000},
    {"grant_name": "Filfox explorer", "batch": "Batch2", "oso_project_slug": None, "total_amount": 30000},
    {"grant_name": "Forest - an efficient and lightweight Filecoin Node", "batch": "Batch2", "oso_project_slug": "forest-chainsafe", "total_amount": 504000},
    {"grant_name": "IPNI", "batch": "Batch2", "oso_project_slug": "ipni", "total_amount": 288000},
    {"grant_name": "Lotus Miner + Boost Maintenance", "batch": "Batch2", "oso_project_slug": "lotus-filecoin-project", "total_amount": 50000},
    {"grant_name": "Oku Trade", "batch": "Batch2", "oso_project_slug": "oku-trade", "total_amount": 66000},
    {"grant_name": "OpenModel", "batch": "Batch2", "oso_project_slug": None, "total_amount": 50000},
    {"grant_name": "ProbeLab Gauge for FOC and Retrieval Testing", "batch": "Batch2", "oso_project_slug": "probe-lab", "total_amount": 100000},
    {"grant_name": "Secured Finance", "batch": "Batch2", "oso_project_slug": "secured-finance", "total_amount": 225000},
    {"grant_name": "Venus Maintenance", "batch": "Batch2", "oso_project_slug": "venus-filecoin-project", "total_amount": 300000},
]

ENTITY_TYPES = {
    "cidgravity": "onramp",
    "titannet-dao": "sp_operator",
    "curio-filecoin-project": "infrastructure",
    "drand": "infrastructure",
    "forest-chainsafe": "infrastructure",
    "ipni": "infrastructure",
    "lotus-filecoin-project": "infrastructure",
    "secured-finance": "infrastructure",
    "celtd": "ecosystem_support",
    "fil-builders": "ecosystem_support",
    "filnote": "ecosystem_support",
    "filponto": "ecosystem_support",
    "lynx-26dos": "ecosystem_support",
    "oku-trade": "ecosystem_support",
    "probe-lab": "ecosystem_support",
    "venus-filecoin-project": "ecosystem_support",
    "chainfee-beck-8": "unclassified",
    "evermediavault": "unclassified",
}

# Derive project list from grants config
projects = sorted(set(
    g["oso_project_slug"] for g in GRANTS if g["oso_project_slug"] is not None
))

# --- Step 1: Verify projects exist in the warehouse ---

slugs = ", ".join(f"'{s}'" for s in projects)

print("Verifying projects in filpgf_public...")
verify_df = client.to_pandas(f"""
SELECT DISTINCT oso_project_slug
FROM filecoin.filpgf_public.key_metrics_by_project
WHERE metric_name = 'propgf_funding_usd'
  AND amount > 0
  AND oso_project_slug IN ({slugs})
""")
verified = set(verify_df["oso_project_slug"])
missing = set(projects) - verified
if missing:
    print(f"  WARNING: {missing} not found in key_metrics — may lack data")
print(f"  {len(verified)}/{len(projects)} projects verified")

# --- Step 2: Pull timeseries metrics ---

query = f"""
SELECT
  oso_project_slug,
  CAST(sample_date AS VARCHAR) AS sample_date,
  metric_name,
  metric_display_name,
  metric_units,
  metric_event_source,
  ROUND(amount, 4) AS amount
FROM filecoin.filpgf_public.timeseries_metrics_by_project
WHERE time_interval = 'monthly'
  AND sample_date >= DATE '2026-02-01'
  AND sample_date < DATE '2026-05-01'
  AND oso_project_slug IN ({slugs})
  AND metric_name NOT LIKE 'propgf%'
  AND metric_name NOT LIKE 'retropgf%'
  AND metric_name NOT LIKE 'impact_grants%'
  AND metric_name NOT LIKE 'hackathon%'
  AND metric_name NOT LIKE 'total_funding%'
  AND metric_name NOT LIKE 'funding_disbursement%'
  AND metric_name NOT LIKE 'received_private%'
  AND metric_name NOT LIKE 'program_%'
ORDER BY oso_project_slug, metric_name, sample_date
"""

print("\nQuerying timeseries metrics from filpgf_public...")
df = client.to_pandas(query)
print(f"Got {len(df)} rows, {df['oso_project_slug'].nunique()} projects")

records = df.to_dict("records")

# --- Step 3: Backfill downstream counts ---
# The dependency survey produces static counts that may only appear
# after the evaluation period. Query latest values across all time
# and backfill into the evaluation window. Zero for projects with
# no survey data.

print("\nBackfilling downstream entity counts...")
backfill_query = f"""
SELECT oso_project_slug, metric_name, MAX(amount) AS amount
FROM filecoin.filpgf_public.timeseries_metrics_by_project
WHERE time_interval = 'monthly'
  AND metric_name IN ('downstream_entity_count', 'downstream_onramp_count')
  AND oso_project_slug IN ({slugs})
GROUP BY oso_project_slug, metric_name
"""
bf_df = client.to_pandas(backfill_query)

backfill_values = {}
for _, row in bf_df.iterrows():
    backfill_values[(row["oso_project_slug"], row["metric_name"])] = row["amount"]

has_metric = set()
for r in records:
    if r["metric_name"] in ("downstream_entity_count", "downstream_onramp_count"):
        has_metric.add((r["oso_project_slug"], r["metric_name"]))

dates = sorted(set(r["sample_date"] for r in records))
catalog = {
    "downstream_entity_count": ("Downstream Entities", "count"),
    "downstream_onramp_count": ("Downstream Onramps", "count"),
}

added = 0
for proj in projects:
    for mn, (display, units) in catalog.items():
        if (proj, mn) not in has_metric:
            value = backfill_values.get((proj, mn), 0)
            for d in dates:
                records.append({
                    "oso_project_slug": proj,
                    "sample_date": d,
                    "metric_name": mn,
                    "metric_display_name": display,
                    "metric_units": units,
                    "metric_event_source": "survey_dependency",
                    "amount": value,
                })
                added += 1
            print(f"  {proj}: {mn} = {value}")

print(f"  Added {added} backfilled rows")

# --- Step 4: Summary ---

print("\nProject summary:")
for proj in projects:
    n = len([r for r in records if r["oso_project_slug"] == proj])
    has_ds = any(
        "downstream" in r["metric_name"]
        for r in records
        if r["oso_project_slug"] == proj
    )
    print(f"  {proj}: {n} rows, downstream={has_ds}")

# --- Step 5: Update the HTML ---

with open(HTML_FILE) as f:
    html = f.read()

match = re.search(r"const DATA = ({.*?});\s*\n", html, re.DOTALL)
if not match:
    raise ValueError("Could not find DATA JSON in HTML")

data = json.loads(match.group(1))
print(f"\nOld timeseries: {len(data['timeseries'])} rows")

data["grants"] = GRANTS
data["entity_types"] = ENTITY_TYPES
data["timeseries"] = records

for r in records:
    mn = r["metric_name"]
    if mn not in data["metric_catalog"]:
        data["metric_catalog"][mn] = {
            "metric_display_name": r["metric_display_name"],
            "metric_units": r["metric_units"],
            "metric_event_source": r["metric_event_source"],
        }

print(f"New timeseries: {len(data['timeseries'])} rows")

new_json = json.dumps(data, default=str)
new_html = html[:match.start()] + f"const DATA = {new_json};\n" + html[match.end():]

with open(HTML_FILE, "w") as f:
    f.write(new_html)

print(f"\nUpdated {HTML_FILE} ({len(new_html)} bytes)")
