from datetime import datetime
from dateutil.relativedelta import relativedelta
from google.cloud import bigquery
import os
import pandas as pd


OUTDIR = 'data/_local'
GCP_PROJECT = 'opensource-observer'
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '../../../oso_gcp_credentials.json'
client = bigquery.Client(project=GCP_PROJECT)


def query_grants(incentive, refresh=False, outdir=OUTDIR):
    
    name = incentive['name']
    outpath = f"{outdir}/{name}.csv"
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
        on inc.address = txns.to_address
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


def query_airdrops(incentive, refresh=False, outdir=OUTDIR):
    
    name = incentive['name']
    outpath = f"{outdir}/{name}.csv"
    if os.path.exists(outpath) and not refresh:
        dataframe = pd.read_csv(outpath, index_col=0)
        print("Query loaded from local storage.")
        return dataframe
    
    table = incentive['table']
    date_drop = datetime.strptime(incentive['date'], '%Y-%m-%d')
    start_date = (date_drop - relativedelta(months=6)).strftime('%Y-%m-%d')
    end_date = (date_drop + relativedelta(months=6)).strftime('%Y-%m-%d')
    
    query = f"""    
    
    with eligible_transactions as (
        select
            bucket_week,
            network,            
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
        select lower(address) as address
        from `{table}`
    ),
    tagged_transactions as (
        select
            txns.bucket_week,
            txns.network,
            case when inc.address is not null then true else false end as is_incentivized,
            txns.count_transactions
        from eligible_transactions as txns
        left join incentivized_addresses as inc
        on inc.address = txns.from_address
    )

    select
        bucket_week,
        network,
        is_incentivized,
        sum(count_transactions) as count_transactions
    from tagged_transactions
    group by 1,2,3
    order by 1
    
    """
    
    print("Requesting:\n", query)
    data = client.query(query)
    print("Response returned.")
    
    dataframe = data.to_dataframe()    
    dataframe.to_csv(outpath)
    print("Dataframe stored at:", outpath)
    return dataframe


def query_airdrop_retention(incentive, refresh=False, outdir=OUTDIR):
    
    name = incentive['name']
    date_drop = datetime.strptime(incentive['date'], '%Y-%m-%d')
    start_date = (date_drop - relativedelta(months=6)).strftime('%Y-%m-%d')
    end_date = (date_drop + relativedelta(months=6)).strftime('%Y-%m-%d')

    outpath = f"{outdir}/retention_{name}.csv"
    if os.path.exists(outpath) and not refresh:
        dataframe = pd.read_csv(outpath, index_col=0)
        print("Query loaded from local storage.")
        return dataframe
    
    table = incentive['table']

    query = f"""    
    
    with retention_since_first_action as (
        select
            txn.bucket_week,
            txn.network,
            lower(txn.from_address) as address,
            greatest(0, cast(timestamp_diff(txn.bucket_week, fta.first_active_day, day) / 7 as int64)) as weeks_since,
            inc.address is not null as is_incentivized,
            txn.count_transactions
        from `static_data_sources.weekly_transactions_by_chain` as txn
        join `oso.int_first_time_addresses` as fta
            on lower(txn.from_address) = lower(fta.address)
            and txn.network = upper(fta.chain_name)
        left join `{table}` as inc
            on lower(txn.from_address) = lower(inc.address)
        where lower(txn.from_address) not in (
            select lower(address)
            from `oso.int_potential_bots`
        )
    ),

    retention_since_airdrop as (
        select
            txn.bucket_week,
            txn.network,
            lower(txn.from_address) as address,
            cast(timestamp_diff(txn.bucket_week, timestamp('{date_drop}'), day) / 7 as int64) as weeks_since,
            inc.address is not null as is_incentivized,
            txn.count_transactions
        from `static_data_sources.weekly_transactions_by_chain` as txn
        join `oso.int_first_time_addresses` as fta
            on txn.from_address = fta.address
            and txn.network = upper(fta.chain_name)
        left join `{table}` as inc
            on txn.from_address = inc.address
        where txn.bucket_week between '{start_date}' and '{end_date}'
            and lower(txn.from_address) not in (
                select lower(address)
                from `oso.int_potential_bots`
            )
    )

    select
        weeks_since,
        'first_action' as week_type,
        network,
        is_incentivized,
        approx_count_distinct(address) as count_addresses,
        sum(count_transactions) as total_transactions
    from retention_since_first_action
    group by weeks_since, week_type, network, is_incentivized

    union all

    select
        weeks_since,
        'airdrop' as week_type,
        network,
        is_incentivized,
        approx_count_distinct(address) as count_addresses,
        sum(count_transactions) as total_transactions
    from retention_since_airdrop
    group by weeks_since, week_type, network, is_incentivized
    order by weeks_since
    
    """
    
    print("Requesting:\n", query)
    data = client.query(query)
    print("Response returned.")
    
    dataframe = data.to_dataframe()    
    dataframe.to_csv(outpath)
    print("Dataframe stored at:", outpath)
    return dataframe
