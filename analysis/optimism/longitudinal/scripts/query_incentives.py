from google.cloud import bigquery
import os
import pandas as pd


GCP_PROJECT = 'opensource-observer'
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '../../../oso_gcp_credentials.json'
client = bigquery.Client(project=GCP_PROJECT)


def query_grants(incentive, refresh=False, outdir = 'data/_local/'):
    
    name = incentive['name']
    outpath = f"{outdir}{name}.csv"
    if os.path.exists(outpath) and not refresh:
        dataframe = pd.read_csv(outpath, index_col=0)
        print("Query loaded from local storage.")
        return dataframe
    
    collection = incentive['collection_name']
    date_drop = datetime.strptime(incentive['date'], '%Y-%m-%d')
    start_date = (date_drop - relativedelta(months=6)).strftime('%Y-%m-%d')
    end_date = (date_drop + relativedelta(months=6)).strftime('%Y-%m-%d')
    
    query = f"""    
    
    with eligible_transactions as (
        select
            bucket_week,
            network,
            lower(to_address) as to_address,
            lower(from_address) as from_address,
            count_transactions
        from `static_data_sources.weekly_transactions_by_chain`
        where
            bucket_week between '{start_date}' and '{end_date}'
            and lower(from_address) not in (
                select lower(address)
                from `oso.int_potential_bots`
            )
    ),
    incentivized_addresses as (
        select lower(to_artifact_name) as address
        from `static_data_sources.addresses_by_project`
        where project_name in (
          select project_name
          from `oso.projects_by_collection_v1`
          where collection_name = '{collection}'
        )
    ),
    tagged_transactions as (
        select
            txns.bucket_week,
            txns.network,
            case when inc.address is not null then true else false end as is_incentivized,
            txns.count_transactions
        from eligible_transactions as txns
        left join incentivized_addresses as inc
        on inc.address = txns.to_address or inc.address = txns.from_address
    )

    select
        bucket_week,
        network,
        is_incentivized,
        sum(count_transactions) as count_transactions
    from tagged_transactions
    group by bucket_week, network, is_incentivized
    order by bucket_week;

    """
    
    print("Requesting:\n", query)
    data = client.query(query)
    print("Response returned.")
    
    dataframe = data.to_dataframe()    
    dataframe.to_csv(outpath)
    print("Dataframe stored at:", outpath)
    return dataframe


def query_airdrops(incentive, refresh=False, outdir = 'data/_local/'):
    
    name = incentive['name']
    outpath = f"{outdir}{name}.csv"
    if os.path.exists(outpath) and not refresh:
        dataframe = pd.read_csv(outpath, index_col=0)
        print("Query loaded from local storage.")
        return dataframe
    
    table = incentive['table']
    table_col = incentive['table_col']
    address_col = incentive['address_col']
    
    date_drop = datetime.strptime(incentive['date'], '%Y-%m-%d')
    start_date = (date_drop - relativedelta(months=6)).strftime('%Y-%m-%d')
    end_date = (date_drop + relativedelta(months=6)).strftime('%Y-%m-%d')
    
    query = f"""    
    
    with eligible_transactions as (
        select
            bucket_week,
            network,
            lower(to_address) as to_address,
            lower(from_address) as from_address,
            count_transactions
        from `static_data_sources.weekly_transactions_by_chain`
        where
            bucket_week between '{start_date}' and '{end_date}'
            and lower(from_address) not in (
                select lower(address)
                from `oso.int_potential_bots`
            )
    ),
    incentivized_addresses as (
        select lower({table_col}) as address
        from `{table}`
    ),
    tagged_transactions as (
        select
            txns.bucket_week,
            txns.network,
            case when inc.address is not null then true else false end as is_incentivized,
            txns.count_transactions
        from eligible_transactions txns
        left join incentivized_addresses inc
        on inc.address = txns.to_address or inc.address = txns.from_address
    )

    select
        bucket_week,
        network,
        is_incentivized,
        sum(count_transactions) as count_transactions
    from tagged_transactions
    group by bucket_week, network, is_incentivized
    order by bucket_week;
    
    """
    
    print("Requesting:\n", query)
    data = client.query(query)
    print("Response returned.")
    
    dataframe = data.to_dataframe()    
    dataframe.to_csv(outpath)
    print("Dataframe stored at:", outpath)
    return dataframe

