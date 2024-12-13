import argparse
import os
import pandas as pd
import numpy as np
from google.cloud import bigquery
from dotenv import load_dotenv
import plotly.graph_objects as go


DEFAULT_COLLECTION = 'op-retrofunding-4'
DEFAULT_OUTPUT_FILE = 'dependency_data_backup.csv'
DEFAULT_HEIGHT = 1200
DEFAULT_WIDTH = 2500
RELEVANT_NETWORKS = ['OPTIMISM', 'BASE', 'MODE', 'ZORA']


def load_env_variables():
    load_dotenv()
    gcp_project = os.getenv('GCP_PROJECT')
    gcp_credentials = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')

    if not gcp_project or not gcp_credentials:
        raise EnvironmentError("GCP_PROJECT or GOOGLE_APPLICATION_CREDENTIALS not set in the environment.")

    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = gcp_credentials
    return gcp_project



class BigQueryFetcher:
    def __init__(self, project):
        self.client = bigquery.Client(project)

    def fetch_data(self, collection):
        query = """
        SELECT
          onchain_projects.project_name AS `Onchain Builder`,
          code_metrics.project_name AS `Dev Tool Maintainer`,
          package_owners.package_artifact_source AS `Package Source`,
          onchain_metrics.event_source AS `Network`,
          ROUND(code_metrics.active_developer_count_6_months, 0) AS developers_6_months,
          onchain_metrics.transaction_count_6_months AS transactions_6_months,
          COUNT(DISTINCT package_owners.package_artifact_name) AS num_packages_maintained
        FROM `oso.sboms_v0` sboms
        JOIN `oso.projects_v1` onchain_projects
          ON sboms.from_project_id = onchain_projects.project_id
        JOIN `oso.projects_by_collection_v1` projects_by_collection
          ON onchain_projects.project_id = projects_by_collection.project_id
        JOIN `oso.onchain_metrics_by_project_v1` onchain_metrics
          ON onchain_projects.project_id = onchain_metrics.project_id
        JOIN `oso.package_owners_v0` package_owners
          ON sboms.to_package_artifact_name = package_owners.package_artifact_name
        JOIN `oso.code_metrics_by_project_v1` code_metrics
          ON package_owners.package_owner_project_id = code_metrics.project_id
        WHERE projects_by_collection.collection_name = @collection
        GROUP BY 1, 2, 3, 4, 5, 6
        ORDER BY 1
        """

        job_config = bigquery.QueryJobConfig(
            query_parameters=[bigquery.ScalarQueryParameter("collection", "STRING", collection)]
        )
        print("Executing BigQuery...")
        result = self.client.query(query, job_config=job_config)
        df = result.to_dataframe()
        print("Query completed successfully.")
        return df


def process_data(df):

    df = df[df['Network'].isin(RELEVANT_NETWORKS)]
    df = df[df['transactions_6_months'] > 10_000]

    usage_count = df.groupby('Dev Tool Maintainer')['Onchain Builder'].nunique()
    df['usage_count'] = df['Dev Tool Maintainer'].map(usage_count)
    df = df[df['usage_count'] > 3]

    df['total_dependencies'] = df.groupby('Onchain Builder')['Dev Tool Maintainer'].transform('nunique')
    df['amount'] = df['transactions_6_months'] / df['total_dependencies']

    overlap = set(df['Onchain Builder']).intersection(df['Dev Tool Maintainer'])
    df['Dev Tool Maintainer'] = df['Dev Tool Maintainer'].apply(
        lambda x: x if x not in overlap else f"{x} [pkg]"
    )
    return df


def generate_sankey(df, category_columns, value_column, title, width, height):
    
    all_labels = list(pd.unique(df[category_columns].values.ravel('K')))
    label_indices = {label: idx for idx, label in enumerate(all_labels)}

    links = []
    for i in range(len(category_columns) - 1):
        temp = df.groupby([category_columns[i], category_columns[i + 1]])[value_column].sum().reset_index()
        temp['source'] = temp[category_columns[i]].map(label_indices)
        temp['target'] = temp[category_columns[i + 1]].map(label_indices)
        links.append(temp)

    link_df = pd.concat(links)

    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=10, thickness=15,
            label=all_labels
        ),
        link=dict(
            source=link_df['source'],
            target=link_df['target'],
            value=link_df[value_column],
            line=dict(color='lightgray', width=0.1)
        )
    )])

    fig.update_layout(title_text=title, height=height, width=width, font=dict(size=10))
    return fig


def main():
    parser = argparse.ArgumentParser(description='Generate dependency analysis visualization')
    parser.add_argument('--bigquery', action='store_true', help='Fetch data from BigQuery')
    parser.add_argument('--collection', type=str, default=DEFAULT_COLLECTION, help='Collection name for analysis')
    parser.add_argument('--height', type=int, default=DEFAULT_HEIGHT, help='Visualization height')
    parser.add_argument('--width', type=int, default=DEFAULT_WIDTH, help='Visualization width')
    args = parser.parse_args()

    gcp_project = load_env_variables()

    if args.bigquery:
        fetcher = BigQueryFetcher(gcp_project)
        df = fetcher.fetch_data(args.collection)
        df.to_csv(DEFAULT_OUTPUT_FILE, index=False)
    else:
        if os.path.exists(DEFAULT_OUTPUT_FILE):
            print("Loading local backup data...")
            df = pd.read_csv(DEFAULT_OUTPUT_FILE)
        else:
            print("Backup file not found. Fetching from BigQuery...")
            fetcher = BigQueryFetcher(gcp_project)
            df = fetcher.fetch_data(args.collection)
            df.to_csv(DEFAULT_OUTPUT_FILE, index=False)

    df = process_data(df)
    fig = generate_sankey(
        df,
        category_columns=['Package Source', 'Dev Tool Maintainer', 'Onchain Builder', 'Network'],
        value_column='amount',
        title="Dependency Graph for Onchain Builders",
        width=args.width,
        height=args.height
    )
    fig.show()


if __name__ == '__main__':
    main()