import pandas as pd

DEFILLAMA_PROTOCOLS = [
    "uniswap-v2",
    "uniswap-v3",
    "bmx-classic-perps",
    "bmx-freestyle",
    "bmx-classic-amm",
    "extra-finance-leverage-farming",
    'hermes-v2',
    "sakefinance"
]

CHAINS = [
    'base',
    'bob',
    'frax',
    'ink',
    'kroma',
    'lisk',
    'lyra',
    'metal',
    'mint',
    'mode',
    'optimism',
    'orderly',
    'polynomial',
    'race',
    'redstone',
    'shape',
    'soneium',
    'swan',
    'swell',
    'unichain',
    'worldchain',
    'xterio',
    'zora',
]

START_DATE = '2025-01-01'
END_DATE = '2025-03-01'
OUTPUT_FILENAME = 'data/defillama_tvls.sql'

def main():
    df = pd.read_parquet('data/enriched_tvl_events.parquet')
    df['amount'] = df['amount'].apply(int)
    df = df[df['event_type'] == 'TVL']
    df = df[['time', 'to_artifact_name', 'from_artifact_namespace', 'amount']]
    df = df[
        (df['to_artifact_name'].isin(DEFILLAMA_PROTOCOLS))
        & (df['from_artifact_namespace'].isin(CHAINS))
        & (df['time'] >= START_DATE)
        & (df['time'] < END_DATE)
    ]
    df.columns = ['bucket_day', 'slug', 'chain', 'amount']
    df.sort_values(by=['slug', 'chain', 'bucket_day'], inplace=True)

    sql_header = (
        "defillama_tvls AS (\n"
        "  SELECT\n"
        "    chain,\n"
        "    slug,\n"
        "    bucket_day,\n"
        "    amount\n"
        "  FROM (VALUES\n"
    )
    values_rows = []
    for _, row in df.iterrows():
        date_only = row['bucket_day'].split()[0]
        values_rows.append(f"    ('{row['chain']}', '{row['slug']}', '{date_only}', {row['amount']})")

    values_section = ",\n".join(values_rows)

    sql_footer = (
        "\n  ) AS x (chain, slug, bucket_day, amount)\n"
        "),\n"
    )

    sql_full = sql_header + values_section + sql_footer

    with open(OUTPUT_FILENAME, "w") as f:
        f.write(sql_full)

    print(f"SQL file '{OUTPUT_FILENAME}' has been written.")


if __name__ == "__main__":
    main()
