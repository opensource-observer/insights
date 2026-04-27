"""
Filecoin PGF data query tool.

Connects to the OSO data warehouse and runs Trino SQL queries against
Filecoin ecosystem data: funding, developer activity, onchain metrics,
dependencies, milestones, and network health.

Setup:
    pip install pyoso  # or: uv add pyoso
    export OSO_API_KEY=<your_filecoin_scoped_key>

Usage:
    python query.py "SELECT display_name FROM filecoin.filpgf_public.projects LIMIT 5"
    python query.py "Show me the top funded projects"

The first argument can be either raw SQL or a natural language question.
If it looks like SQL (starts with SELECT, WITH, etc.), it runs directly.
Otherwise it's treated as a question and matched to a query template.
"""

import sys
import os

try:
    from pyoso import Client
except ImportError:
    print("pyoso not installed. Run: pip install pyoso")
    sys.exit(1)


def get_client():
    if not os.environ.get("OSO_API_KEY"):
        print("OSO_API_KEY not set. Get one at https://www.oso.xyz/start")
        print("Must be scoped to the Filecoin organization.")
        sys.exit(1)
    return Client()


TEMPLATES = {
    "projects": """
        SELECT oso_project_slug, display_name
        FROM filecoin.filpgf_public.projects
        ORDER BY display_name
    """,
    "top funded": """
        SELECT
          p.oso_project_slug,
          p.display_name,
          MAX(CASE WHEN k.metric_name = 'total_funding_usd' THEN k.amount END) AS total_usd,
          MAX(CASE WHEN k.metric_name = 'total_funding_fil' THEN k.amount END) AS total_fil
        FROM filecoin.filpgf_public.projects AS p
        INNER JOIN filecoin.filpgf_public.key_metrics_by_project AS k
          ON p.oso_project_slug = k.oso_project_slug
        WHERE k.metric_name IN ('total_funding_usd', 'total_funding_fil')
        GROUP BY p.oso_project_slug, p.display_name
        ORDER BY total_usd DESC NULLS LAST
        LIMIT 30
    """,
    "metrics": """
        SELECT metric_name, metric_display_name, metric_units, metric_category
        FROM filecoin.filpgf_public.metric_catalog
        ORDER BY metric_category, metric_name
    """,
    "network": """
        SELECT sample_date, metric_name, amount
        FROM filecoin.filpgf_public.timeseries_metrics_by_network
        WHERE metric_name IN (
          'network_raw_power_pibs', 'network_daily_onboarding_tibs',
          'fil_price_usd', 'network_block_rewards_fil'
        )
        AND time_interval = 'daily'
        AND sample_date >= CURRENT_DATE - INTERVAL '30' DAY
        ORDER BY sample_date, metric_name
    """,
    "developer activity": """
        SELECT sample_date, metric_name, SUM(amount) AS total
        FROM filecoin.filpgf_public.timeseries_metrics_by_project
        WHERE metric_name IN ('commits', 'active_developers_28d')
          AND time_interval = 'monthly'
        GROUP BY sample_date, metric_name
        ORDER BY sample_date
    """,
    "funding by program": """
        SELECT sample_date, metric_name, SUM(amount) AS total
        FROM filecoin.filpgf_public.timeseries_metrics_by_program
        WHERE metric_name IN ('propgf_amount_usd', 'retropgf_amount_fil', 'impact_grants_amount_fil')
          AND time_interval = 'monthly'
        GROUP BY sample_date, metric_name
        ORDER BY sample_date
    """,
}


def looks_like_sql(text):
    first_word = text.strip().split()[0].upper() if text.strip() else ""
    return first_word in ("SELECT", "WITH", "SHOW", "DESCRIBE", "EXPLAIN")


def match_template(question):
    q = question.lower()
    for key, sql in TEMPLATES.items():
        if key in q:
            return sql
    return None


def run_query(sql):
    client = get_client()
    df = client.to_pandas(sql)
    return df


def project_metrics(slug):
    """Get all snapshot metrics for a project."""
    sql = f"""
        SELECT metric_name, amount, metric_units
        FROM filecoin.filpgf_public.key_metrics_by_project
        WHERE oso_project_slug = '{slug}'
        ORDER BY metric_name
    """
    return run_query(sql)


def project_timeseries(slug, metrics, interval="monthly"):
    """Get timeseries for specific metrics on a project."""
    metric_list = ", ".join(f"'{m}'" for m in metrics)
    sql = f"""
        SELECT sample_date, metric_name, amount
        FROM filecoin.filpgf_public.timeseries_metrics_by_project
        WHERE oso_project_slug = '{slug}'
          AND metric_name IN ({metric_list})
          AND time_interval = '{interval}'
        ORDER BY sample_date
    """
    return run_query(sql)


def project_milestones(slug):
    """Get Karma milestones for a project via the bridge table."""
    bridge_sql = f"""
        SELECT karma_slug, karma_title
        FROM filecoin.entities.bridge_karma_to_oso
        WHERE oso_project_slug = '{slug}'
        LIMIT 1
    """
    bridge_df = run_query(bridge_sql)
    if bridge_df.empty:
        return None, f"No Karma profile found for '{slug}'"

    karma_slug = bridge_df.iloc[0]["karma_slug"]
    karma_title = bridge_df.iloc[0]["karma_title"]
    milestone_sql = f"""
        SELECT
          milestone_title,
          current_status,
          ends_at,
          status_updated_at
        FROM filecoin.karma_milestones.milestones
        WHERE karma_slug = '{karma_slug}'
        ORDER BY ends_at
    """
    return run_query(milestone_sql), karma_title


def main():
    if len(sys.argv) < 2:
        print("Usage: python query.py <sql_or_question>")
        print()
        print("Examples:")
        print('  python query.py "SELECT * FROM filecoin.filpgf_public.projects LIMIT 5"')
        print('  python query.py "top funded"')
        print('  python query.py "metrics"')
        print('  python query.py "network"')
        print()
        print(f"Available templates: {', '.join(TEMPLATES.keys())}")
        sys.exit(0)

    query = " ".join(sys.argv[1:])

    if looks_like_sql(query):
        sql = query
    else:
        sql = match_template(query)
        if sql is None:
            print(f"No template matched for: {query}")
            print(f"Available: {', '.join(TEMPLATES.keys())}")
            print("Or pass raw SQL directly.")
            sys.exit(1)

    df = run_query(sql)
    print(df.to_string(index=False))


if __name__ == "__main__":
    main()
