from dotenv import load_dotenv
import os
import pandas as pd
from pyoso import Client
from datetime import datetime, date
from dateutil.relativedelta import relativedelta


def fetch_github_metrics(client):
    """Fetch GitHub metrics for Stylus Sprint projects"""
    query = """
        SELECT  distinct p.display_name as display_name,
                p.project_name as project_name,
                m.metric_name as metric_name,
                ts.sample_date as sample_date,
                ts.amount as amount
        FROM metrics_v0 m
        JOIN timeseries_metrics_by_project_v0 ts
        on m.metric_id = ts.metric_id
        JOIN projects_v1 p
        on p.project_id = ts.project_id
        JOIN projects_by_collection_v1 pc
        on p.project_id = pc.project_id
        where metric_name like 'GITHUB_%'
        and YEAR(ts.sample_date) in (2022, 2023, 2024, 2025)
        and pc.collection_name = 'arb-stylus'
    """
    df = client.to_pandas(query)
    df['sample_date'] = pd.to_datetime(df['sample_date'])
    return df

def fetch_github_metrics_repo(client):
    """Fetch GitHub metrics for Repos of Stylus Sprint projects"""
    query = """
    SELECT  ap.artifact_name as artifact_name, 
            ap.project_name as project_name,
            m.metric_name as metric_name,
            ts.sample_date as sample_date,
            ts.amount as amount
    FROM int_artifacts_by_project ap
    JOIN projects_by_collection_v1 pc
    on ap.project_id = pc.project_id
    JOIN timeseries_metrics_by_artifact_v0 ts
    on ts.artifact_id = ap.artifact_id
    JOIN metrics_v0 m
    ON m.metric_id = ts.metric_id
    where pc.collection_name = 'arb-stylus'
    and ap.artifact_source = 'GITHUB'
    and m.metric_name = 'GITHUB_active_developers_monthly'
    and YEAR(ts.sample_date) in (2022, 2023, 2024, 2025)
    """
    df = client.to_pandas(query)
    df['sample_date'] = pd.to_datetime(df['sample_date'])
    return df

def fetch_sdk_dependencies(client):
    """Fetch Stylus SDK dependencies"""
    query = """
    WITH seed_repos AS (
      SELECT DISTINCT 
        sboms.from_artifact_namespace,
        sboms.from_artifact_name
      FROM sboms_v0 sboms
      JOIN package_owners_v0 package_owners
        ON sboms.to_package_artifact_name = package_owners.package_artifact_name
        AND sboms.to_package_artifact_source = package_owners.package_artifact_source
      WHERE package_owners.package_owner_artifact_namespace = 'offchainlabs'
        AND package_owners.package_owner_artifact_name = 'stylus-sdk-rs'
    )
    SELECT DISTINCT
      sboms.from_artifact_namespace as seed_repo_owner,
      sboms.from_artifact_name as seed_repo_name,
      sboms.to_package_artifact_name as package_name,
      package_owners.package_owner_artifact_namespace as package_repo_owner,
      package_owners.package_owner_artifact_name as package_repo_name,
      sboms.to_package_artifact_source as package_source
    FROM sboms_v0 sboms
    JOIN package_owners_v0 package_owners
      ON sboms.to_package_artifact_name = package_owners.package_artifact_name
      AND sboms.to_package_artifact_source = package_owners.package_artifact_source
    JOIN seed_repos
      ON sboms.from_artifact_namespace = seed_repos.from_artifact_namespace
      AND sboms.from_artifact_name = seed_repos.from_artifact_name
    WHERE package_owners.package_owner_artifact_namespace IS NOT NULL
    """
    return client.to_pandas(query)

def fetch_dependencies_by_project(client):
    # Calculate previous month's start and end dates
    today = date.today()
    first_day_of_prev_month = today.replace(day=1) - relativedelta(months=1)
    last_day_of_prev_month = today.replace(day=1) - relativedelta(days=1)

    # First, get projects dependent on grantees in Stylus Sprint and then get no. of active developers for each project.
    query = f"""
    WITH sbom_links AS (
        SELECT distinct
            sboms.from_artifact_namespace,
            sboms.from_artifact_name,
            sboms.to_package_artifact_name,
            sboms.to_package_artifact_source,
            po.package_owner_artifact_namespace
        FROM package_owners_v0 po
        JOIN projects_by_collection_v1 pc
            ON po.package_owner_artifact_namespace = pc.project_name
        JOIN sboms_v0 sboms
            ON sboms.to_package_artifact_name = po.package_artifact_name
            AND sboms.to_package_artifact_source = po.package_artifact_source
        WHERE pc.collection_name = 'arb-stylus'
    )

    SELECT  
        ap.artifact_name,
        ap.project_name,
        m.metric_name,
        ts.sample_date,
        ts.amount,
        sb.from_artifact_namespace,
        sb.from_artifact_name,
        sb.to_package_artifact_name,
        sb.to_package_artifact_source,
        sb.package_owner_artifact_namespace
    FROM sbom_links sb
    JOIN artifacts_by_project_v1 ap
        ON sb.from_artifact_namespace = ap.artifact_namespace
        AND sb.from_artifact_name = ap.artifact_name
    JOIN timeseries_metrics_by_artifact_v0 ts
        ON ts.artifact_id = ap.artifact_id
    JOIN metrics_v0 m
        ON m.metric_id = ts.metric_id
    WHERE ap.artifact_source = 'GITHUB'
      AND m.metric_name = 'GITHUB_active_developers_monthly'
      AND ts.sample_date BETWEEN DATE '{first_day_of_prev_month}' AND DATE '{last_day_of_prev_month}'
    """
    return client.to_pandas(query)

def fetch_project_orgs(client):
    """Fetch Github orgs for projects in Stylus"""
    query = """
        SELECT  p.display_name as display_name,
                p.project_name as project_name,
                a.artifact_namespace as artifact_namespace
        FROM projects_by_collection_v1 pc
        join projects_v1 p 
        on pc.project_id = p.project_id
        left join int_artifacts_by_project a
        on p.project_id = a.project_id
        and a.artifact_source = 'GITHUB'
        where collection_name = 'arb-stylus'    
        group by 1,2,3
    """
    return client.to_pandas(query)

def fetch_arb_projects_active_devs(client):
    """Fetch active developers for Arbitrum projects in OSSD"""
    query = """
        WITH arb_projects AS (
            SELECT distinct project_id
            FROM int_artifacts_by_project_in_ossd
            WHERE artifact_source = 'ARBITRUM_ONE'
            AND artifact_type IN ('CONTRACT', 'FACTORY', 'DEPLOYER')
        )
        SELECT  distinct p.display_name as display_name,
                m.metric_name as metric_name,
                ts.sample_date as sample_date,
                ts.amount as amount
        FROM metrics_v0 m
        JOIN timeseries_metrics_by_project_v0 ts
        on m.metric_id = ts.metric_id
        JOIN projects_v1 p
        on p.project_id = ts.project_id
        JOIN arb_projects a
        on p.project_id = a.project_id
        where metric_name = 'GITHUB_active_developers_monthly'
        and YEAR(ts.sample_date) in (2022, 2023, 2024, 2025)
    """
    df = client.to_pandas(query)
    df['sample_date'] = pd.to_datetime(df['sample_date'])
    return df

def fetch_stylus_deps_active_devs(client):
    """Fetch active developers for Stylus SDK dependencies"""
    query = """
      WITH dep_projects AS (
      SELECT distinct sboms.from_project_id
      FROM sboms_v0 sboms
      JOIN package_owners_v0 package_owners
        ON sboms.to_package_artifact_name = package_owners.package_artifact_name
        AND sboms.to_package_artifact_source = package_owners.package_artifact_source
      WHERE package_owners.package_owner_artifact_namespace = 'offchainlabs'
        AND package_owners.package_owner_artifact_name = 'stylus-sdk-rs'
      )
       SELECT  distinct p.display_name as display_name,
                m.metric_name as metric_name,
                ts.sample_date as sample_date,
                ts.amount as amount
        FROM metrics_v0 m
        JOIN timeseries_metrics_by_project_v0 ts
        on m.metric_id = ts.metric_id
        JOIN projects_v1 p
        on p.project_id = ts.project_id
        JOIN dep_projects a
        on p.project_id = a.from_project_id
        where metric_name = 'GITHUB_active_developers_monthly'
        and YEAR(ts.sample_date) in (2022, 2023, 2024, 2025)
    """
    df = client.to_pandas(query)
    df['sample_date'] = pd.to_datetime(df['sample_date'])
    return df

def main():
    # Load environment variables
    load_dotenv()
    OSO_API_KEY = os.environ['OSO_API_KEY']
    client = Client(api_key=OSO_API_KEY)

    # Create data directory if it doesn't exist
    os.makedirs('data', exist_ok=True)

    # Fetch and save all data
    print("Fetching Org Level GitHub metrics...")
    github_metrics = fetch_github_metrics(client)
    github_metrics.to_csv('./data/stylus_github_metrics.csv', index=False)
   
    print("Fetching Repo Level GitHub metrics...")
    github_metrics_repo  = fetch_github_metrics_repo(client)
    github_metrics_repo.to_csv('./data/stylus_github_metrics_repo.csv', index=False)

    print("Fetching Stylus SDK dependencies...")
    sdk_deps = fetch_sdk_dependencies(client)
    sdk_deps.to_csv('./data/stylus-sdk-rs-dependencies.csv', index=False)

    print("Fetching projects dependencies...")
    project_deps = fetch_dependencies_by_project(client)
    project_deps.to_csv('./data/project_dependencies.csv', index=False)

    print("Fetching project organizations...")
    project_orgs = fetch_project_orgs(client)
    project_orgs.to_csv('./data/project_orgs.csv', index=False)

    print("Fetching Arbitrum projects active developers...")
    arb_devs = fetch_arb_projects_active_devs(client)
    arb_devs.to_csv('./data/arb_projects_active_dev_monthly.csv', index=False)

    print("Fetching Stylus dependencies active developers...")
    stylus_deps_devs = fetch_stylus_deps_active_devs(client)
    stylus_deps_devs.to_csv('./data/stylus_dependencies_active_dev_monthly.csv', index=False)

    print("Data refresh completed successfully!")

if __name__ == "__main__":
    main() 