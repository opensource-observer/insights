from google.cloud import bigquery
import json
import os


CURRENT_DIR = os.path.dirname(__file__)
DATA_PATH = os.path.join(CURRENT_DIR, '../data/_local/farcaster.json')
CREDENTIALS_PATH = os.path.join(CURRENT_DIR, '../../../oso_gcp_credentials.json')
GCP_PROJECT = 'opensource-observer'


def refresh_farcaster():
    client = bigquery.Client(project=GCP_PROJECT)
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = CREDENTIALS_PATH
    query = f"""
        WITH
        profiles AS (
            SELECT
                v.fid,
                v.address,
                p.custody_address,
                p.username
            FROM `{GCP_PROJECT}.farcaster.verifications` v
            JOIN `{GCP_PROJECT}.oso.stg_farcaster__profiles` p
                ON v.fid = CAST(p.farcaster_id AS int64)
            WHERE v.deleted_at IS NULL
        ),
        eth_addresses AS (
            SELECT
                fid,
                address,
                username
            FROM profiles
            WHERE LENGTH(address) = 42
            UNION ALL
            SELECT
                fid,
                custody_address AS address,
                username
            FROM profiles
        )
        SELECT DISTINCT
            fid,
            address,
            username
        FROM eth_addresses
    """

    result = client.query(query)
    farcaster = result.to_dataframe()
    farcaster.to_json(DATA_PATH, orient='records', lines=False)
    print(f"Refreshed Farcaster data at {DATA_PATH}")


def load_farcaster():
    if os.path.exists(DATA_PATH):
        with open(DATA_PATH, 'r') as f:
            farcaster = json.load(f)
    else:
        print(f"No data file found at {DATA_PATH}")
        refresh_farcaster()
        return load_farcaster()
    return farcaster


if __name__ == "__main__":
    refresh_farcaster()