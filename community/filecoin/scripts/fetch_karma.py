"""
Fetch Filecoin grant and milestone data from the Karma GAP API.

No API key required. Rate limit: ~200 requests per 60s window.

Usage:
    uv run fetch_karma.py                          # all Filecoin grants
    uv run fetch_karma.py --project lighthouse      # single project by slug
    uv run fetch_karma.py --output karma.csv        # save to CSV
    uv run fetch_karma.py --milestones-only         # just milestones table
"""

import argparse
import json
import sys
import time
from urllib.request import urlopen, Request
from urllib.error import HTTPError

BASE_URL = "https://gapapi.karmahq.xyz"
COMMUNITY_SLUG = "filecoin"


def api_get(path, params=None):
    url = f"{BASE_URL}{path}"
    if params:
        query = "&".join(f"{k}={v}" for k, v in params.items())
        url = f"{url}?{query}"
    req = Request(url, headers={"Accept": "application/json"})
    try:
        with urlopen(req) as resp:
            return json.loads(resp.read())
    except HTTPError as e:
        if e.code == 429:
            print("Rate limited. Waiting 60s...", file=sys.stderr)
            time.sleep(60)
            with urlopen(req) as resp:
                return json.loads(resp.read())
        raise


def fetch_community_grants(page_limit=100):
    data = api_get(
        f"/communities/{COMMUNITY_SLUG}/grants",
        {"pageLimit": str(page_limit)},
    )
    return data.get("data", data) if isinstance(data, dict) else data


def fetch_project(slug):
    data = api_get(f"/projects/{slug}")
    return data.get("data", data) if isinstance(data, dict) else data


def fetch_project_grants(slug):
    data = api_get(f"/projects/{slug}/grants")
    return data.get("data", data) if isinstance(data, dict) else data


def extract_grants_table(grants):
    rows = []
    for g in grants:
        details = g.get("details", {})
        project = g.get("project", {})
        project_details = project.get("details", {}).get("data", {})
        milestones = g.get("milestones", [])

        completed = sum(
            1
            for m in milestones
            if m.get("currentStatus") in ("completed", "verified", "approved")
        )

        rows.append(
            {
                "grant_uid": g.get("uid", ""),
                "project_title": project_details.get("title", ""),
                "project_slug": project_details.get("slug", ""),
                "grant_title": details.get("title", ""),
                "program_id": g.get("programId", ""),
                "amount": details.get("amount", ""),
                "currency": details.get("currency", ""),
                "proposal_url": details.get("proposalURL", ""),
                "payout_address": details.get("payoutAddress", ""),
                "start_date": details.get("startDate", ""),
                "is_completed": details.get("isCompleted", False),
                "milestone_count": len(milestones),
                "milestones_done": completed,
                "categories": ", ".join(g.get("categories", [])),
            }
        )
    return rows


def extract_milestones_table(grants):
    rows = []
    for g in grants:
        details = g.get("details", {})
        project = g.get("project", {})
        project_details = project.get("details", {}).get("data", {})

        for m in g.get("milestones", []):
            completed_info = m.get("completed", {}) or {}
            verified_list = m.get("verified", []) or []

            rows.append(
                {
                    "project_slug": project_details.get("slug", ""),
                    "project_title": project_details.get("title", ""),
                    "grant_title": details.get("title", ""),
                    "milestone_uid": m.get("uid", ""),
                    "milestone_title": m.get("title", ""),
                    "milestone_description": m.get("description", ""),
                    "due_date": m.get("dueDate", ""),
                    "current_status": m.get("currentStatus", ""),
                    "status_updated_at": m.get("statusUpdatedAt", ""),
                    "proof_of_work": completed_info.get("proofOfWork", ""),
                    "completion_reason": completed_info.get("reason", ""),
                    "verified_count": len(verified_list),
                }
            )
    return rows


def print_table(rows, columns=None):
    if not rows:
        print("No data found.")
        return
    if columns is None:
        columns = list(rows[0].keys())
    widths = {c: max(len(c), max(len(str(r.get(c, ""))) for r in rows)) for c in columns}
    header = " | ".join(c.ljust(widths[c]) for c in columns)
    separator = "-+-".join("-" * widths[c] for c in columns)
    print(header)
    print(separator)
    for r in rows:
        print(" | ".join(str(r.get(c, "")).ljust(widths[c]) for c in columns))


def write_csv(rows, path):
    if not rows:
        print("No data to write.", file=sys.stderr)
        return
    import csv

    columns = list(rows[0].keys())
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} rows to {path}", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(description="Fetch Filecoin data from Karma GAP API")
    parser.add_argument("--project", help="Fetch grants for a specific project slug")
    parser.add_argument("--output", "-o", help="Save output to CSV file")
    parser.add_argument(
        "--milestones-only",
        action="store_true",
        help="Output milestones table instead of grants summary",
    )
    parser.add_argument("--json", action="store_true", help="Output raw JSON")
    args = parser.parse_args()

    if args.project:
        print(f"Fetching grants for project: {args.project}", file=sys.stderr)
        grants = fetch_project_grants(args.project)
    else:
        print(f"Fetching all {COMMUNITY_SLUG} grants...", file=sys.stderr)
        grants = fetch_community_grants()

    if not grants:
        print("No grants found.", file=sys.stderr)
        sys.exit(1)

    if args.json:
        print(json.dumps(grants, indent=2))
        return

    if args.milestones_only:
        rows = extract_milestones_table(grants)
    else:
        rows = extract_grants_table(grants)

    if args.output:
        write_csv(rows, args.output)
    else:
        summary_cols = (
            ["project_slug", "milestone_title", "due_date", "current_status", "proof_of_work"]
            if args.milestones_only
            else [
                "project_slug",
                "grant_title",
                "program_id",
                "amount",
                "milestone_count",
                "milestones_done",
            ]
        )
        print_table(rows, columns=summary_cols)


if __name__ == "__main__":
    main()
