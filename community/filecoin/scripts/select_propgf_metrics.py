"""Pull complete timeseries data via pyoso and rebuild the form HTML.

Queries the warehouse for all Pro PGF project metrics, backfills
downstream entity counts for projects missing survey data, and
updates the embedded JSON in the metric selection form.

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

PROJECTS = [
    "celtd", "chainfee-beck-8", "cidgravity", "curio-filecoin-project",
    "drand", "evermediavault", "fil-builders", "filnote", "filponto",
    "forest-chainsafe", "ipni", "lotus-filecoin-project", "lynx-26dos",
    "oku-trade", "probe-lab", "secured-finance", "titannet-dao",
    "venus-filecoin-project",
]

HTML_FILE = Path(__file__).parent.parent / "examples" / "propgf-metric-selection.html"

slugs = ", ".join(f"'{s}'" for s in PROJECTS)

# --- Step 1: Pull timeseries metrics ---

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

print("Querying timeseries metrics...")
df = client.to_pandas(query)
print(f"Got {len(df)} rows, {df['oso_project_slug'].nunique()} projects")

records = df.to_dict("records")

# --- Step 2: Backfill downstream counts for projects missing them ---
# The dependency survey produces static counts that may only appear in
# months after the survey ran. We query the latest values and backfill
# them across the evaluation period. Projects with no survey data get
# explicit zeros.

print("\nChecking downstream entity counts...")
backfill_query = f"""
SELECT oso_project_slug, metric_name, MAX(amount) AS amount
FROM filecoin.filpgf_public.timeseries_metrics_by_project
WHERE time_interval = 'monthly'
  AND metric_name IN ('downstream_entity_count', 'downstream_onramp_count')
  AND oso_project_slug IN ({slugs})
GROUP BY oso_project_slug, metric_name
"""
bf_df = client.to_pandas(backfill_query)

# Build lookup: (project, metric) -> value
backfill_values = {}
for _, row in bf_df.iterrows():
    backfill_values[(row["oso_project_slug"], row["metric_name"])] = row["amount"]

# Determine which projects already have these metrics in the evaluation period
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
for proj in PROJECTS:
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
            print(f"  {proj}: {mn} = {value} (backfilled)")

print(f"Added {added} backfilled rows")

# --- Step 3: Summary ---

for proj in PROJECTS:
    n = len([r for r in records if r["oso_project_slug"] == proj])
    has_ds = any(
        "downstream" in r["metric_name"]
        for r in records
        if r["oso_project_slug"] == proj
    )
    print(f"  {proj}: {n} rows, downstream={has_ds}")

# --- Step 4: Update the HTML ---

with open(HTML_FILE) as f:
    html = f.read()

match = re.search(r"const DATA = ({.*?});\s*\n", html, re.DOTALL)
if not match:
    raise ValueError("Could not find DATA JSON in HTML")

data = json.loads(match.group(1))
print(f"\nOld timeseries: {len(data['timeseries'])} rows")

for r in records:
    mn = r["metric_name"]
    if mn not in data["metric_catalog"]:
        data["metric_catalog"][mn] = {
            "metric_display_name": r["metric_display_name"],
            "metric_units": r["metric_units"],
            "metric_event_source": r["metric_event_source"],
        }

data["timeseries"] = records
print(f"New timeseries: {len(data['timeseries'])} rows")

new_json = json.dumps(data, default=str)
new_html = html[:match.start()] + f"const DATA = {new_json};\n" + html[match.end():]

with open(HTML_FILE, "w") as f:
    f.write(new_html)

print(f"\nUpdated {HTML_FILE} ({len(new_html)} bytes)")
