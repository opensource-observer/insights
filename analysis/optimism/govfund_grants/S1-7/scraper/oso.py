from dotenv import load_dotenv
import json
import os
import pandas as pd
from pyoso import Client

load_dotenv()
OSO_API_KEY = os.environ['OSO_API_KEY']
oso_client = Client(api_key=OSO_API_KEY)

def fetch_projects():
    query = """
    WITH cte AS (
        SELECT DISTINCT
        p.project_name AS oso_slug,
        p.display_name,
        COALESCE(p.description, '') AS description,
        CASE
            WHEN abp.artifact_type = 'REPOSITORY' THEN CONCAT('https://github.com/', abp.artifact_namespace)
            ELSE abp.artifact_url END
        AS artifact_url
        FROM projects_v1 AS p
        JOIN projects_by_collection_v1 AS pbc ON p.project_id = pbc.project_id
        JOIN int_artifacts_by_project_in_ossd AS abp ON p.project_id = abp.project_id
        WHERE
            pbc.collection_name = 'optimism'
            AND abp.artifact_type IN ('WEBSITE', 'SOCIAL_HANDLE', 'REPOSITORY', 'DEFILLAMA_PROTOCOL')
    )

    SELECT
        oso_slug,
        display_name,
        description,
        ARRAY_AGG(artifact_url) AS urls
    FROM cte
    GROUP BY oso_slug, display_name, description
    ORDER BY LOWER(display_name)
    """

    dataframe = oso_client.to_pandas(query)
    json_records = dataframe.to_dict(orient='records')
    return json_records

if __name__ == "__main__":
    projects = fetch_projects()
    with open('data/oso_projects.json', 'w') as f:
        json.dump(projects, f, indent=2)