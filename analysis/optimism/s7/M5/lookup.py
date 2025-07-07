import pandas as pd
from pyoso import Client
import os
from dotenv import load_dotenv


load_dotenv()
OSO_API_KEY = os.environ['OSO_API_KEY']

if __name__ == "__main__":
    client = Client(api_key=OSO_API_KEY)
    df = client.to_pandas("""
    SELECT DISTINCT
      CONCAT('https://github.com/', b.repo_artifact_namespace, '/', b.repo_artifact_name) AS onchain_builder_repo,
      cd.dependency_name
    FROM int_superchain_s7_devtooling_onchain_builder_nodes AS b
    JOIN int_code_dependencies AS cd ON cd.dependent_artifact_id = b.repo_artifact_id
    JOIN int_superchain_s7_devtooling_repositories AS d
      ON cd.dependency_artifact_id = d.repo_artifact_id
    WHERE
      cd.dependency_source = 'NPM'
      AND b.op_atlas_project_name IS NOT NULL
    """)
    df.to_csv("analysis/optimism/s7/M5/m5_dependencies.csv", index=False)