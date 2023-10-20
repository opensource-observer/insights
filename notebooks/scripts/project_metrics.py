from oso_db import execute_query, execute_saved_query
import time

TABLES = {
    'artifact': ['createdAt', 'updatedAt', 'name', 'url', 'deletedAt', 'namespace', 'type', 'id'],
    'collection': ['deletedAt', 'verified', 'id', 'slug', 'description', 'name', 'createdAt', 'updatedAt'],
    'collection_projects_project': ['projectId', 'collectionId'],
    'event': ['toId', 'amount', 'time', 'details', 'typeId', 'sourceId', 'fromId', 'id'],
    'event_type': ['version', 'deletedAt', 'updatedAt', 'createdAt', 'id', 'name'],
    'project_artifacts_artifact': ['projectId', 'artifactId']
 }

ARTIFACTS = {
    'OPTIMISM': ['EOA_ADDRESS', 'SAFE_ADDRESS', 'CONTRACT_ADDRESS', 'FACTORY_ADDRESS'],
    'GITHUB': ['GIT_REPOSITORY', 'GIT_EMAIL', 'GIT_NAME', 'GITHUB_ORG', 'GITHUB_USER'],
    'NPM_REGISTRY': ['NPM_PACKAGE']
}

EVENT_TYPES = {
    'FUNDING': 1,
    'PULL_REQUEST_CREATED': 2,
    'PULL_REQUEST_MERGED': 3,
    'COMMIT_CODE': 4,
    'ISSUE_FILED': 5,
    'ISSUE_CLOSED': 6,
    'DOWNSTREAM_DEPENDENCY_COUNT': 7,
    'UPSTREAM_DEPENDENCY_COUNT': 8,
    'DOWNLOADS': 9,
    'CONTRACT_INVOKED': 10,
    'USERS_INTERACTED': 11,
    'CONTRACT_INVOKED_AGGREGATE_STATS': 12,
    'PULL_REQUEST_CLOSED': 13,
    'STAR_AGGREGATE_STATS': 14,
    'PULL_REQUEST_REOPENED': 15,
    'PULL_REQUEST_REMOVED_FROM_PROJECT': 16,
    'PULL_REQUEST_APPROVED': 17,
    'ISSUE_CREATED': 18,
    'ISSUE_REOPENED': 19,
    'ISSUE_REMOVED_FROM_PROJECT': 20,
    'STARRED': 21,
    'FORK_AGGREGATE_STATS': 22,
    'FORKED': 23,
    'WATCHER_AGGREGATE_STATS': 24,
    'CONTRACT_INVOCATION_DAILY_COUNT': 25,
    'CONTRACT_INVOCATION_DAILY_FEES': 26
}


def query(query_string, debug=False):
    try:
        if debug:
            print(query_string)
        results = execute_query(query_string)
        if not results:
            print("No results.")
            return []
        if debug and len(results) > 3:
            print(results[:3])
        return [dict(zip(results[0], row)) for row in results[1:]]
    except Exception as e:
        print(f"Error executing query: {e}")
        return query(query_string, debug=True)


def wei_to_eth(wei):
    return wei / 10**18


get_project_id_from_slug = lambda slug: query(f"select id from project where slug = '{slug}'")[0]['id']


get_contracts_that_belong_to_project = lambda project_id: query(f"""
    select distinct on (a.id) a.id, a.name, a.url, a.type, a.namespace
    from artifact a 
    inner join project_artifacts_artifact paa on paa."artifactId" = a.id
    where paa."projectId" = '{project_id}'
    and a.type in ('CONTRACT_ADDRESS', 'FACTORY_ADDRESS')
    and a.namespace = 'OPTIMISM'
""")


get_transactions_for_list_of_contracts = lambda contract_ids: query(f"""
    select e."fromId", e."toId", e."amount", e."time", e."typeId", e."sourceId", e."details", e.id
    from event e
    where e."typeId" = {EVENT_TYPES['CONTRACT_INVOCATION_DAILY_COUNT']}
    and e."toId" in ({",".join(contract_ids)})
""")


get_transaction_count_for_list_of_contracts = lambda contract_ids: query(f"""
    select sum(e."amount") as count
    from event e
    where e."typeId" = {EVENT_TYPES['CONTRACT_INVOCATION_DAILY_COUNT']}
    and e."toId" in ({",".join(contract_ids)})
""")


get_recent_transaction_count_for_list_of_contracts = lambda contract_ids: query(f"""
    select sum(e."amount") as count
    from event e
    where e."typeId" = {EVENT_TYPES['CONTRACT_INVOCATION_DAILY_COUNT']}
    and e."toId" in ({",".join(contract_ids)})
    and e."time" > now() - interval '7 days'
""")


get_transaction_fees_for_list_of_contracts = lambda contract_ids: query(f"""
    select e."fromId", e."toId", e."amount", e."time", e."typeId", e."sourceId", e."details", e.id
    from event e
    where e."typeId" = {EVENT_TYPES['CONTRACT_INVOCATION_DAILY_FEES']}
    and e."toId" in ({",".join(contract_ids)})
""")


get_transaction_fee_sum_for_list_of_contracts = lambda contract_ids: query(f"""
    select sum(e."amount") as fees
    from event e
    where e."typeId" = {EVENT_TYPES['CONTRACT_INVOCATION_DAILY_FEES']}
    and e."toId" in ({",".join(contract_ids)})
""")


get_avg_transaction_fee_for_list_of_contracts = lambda contract_ids: query(f"""
    select 
          sum(CASE WHEN e."typeId" = {EVENT_TYPES['CONTRACT_INVOCATION_DAILY_FEES']} THEN e."amount" ELSE 0 END) 
        / sum(CASE WHEN e."typeId" = {EVENT_TYPES['CONTRACT_INVOCATION_DAILY_COUNT']} THEN e."amount" ELSE 0 END) 
    as fees
    from event e
    where e."typeId" in ({EVENT_TYPES['CONTRACT_INVOCATION_DAILY_FEES']}, {EVENT_TYPES['CONTRACT_INVOCATION_DAILY_COUNT']})
    and e."toId" in ({",".join(contract_ids)})
""")


get_lifetime_users_for_list_of_contracts = lambda contract_ids: query(f"""
    select distinct e."fromId" as user
    from event e
    where e."typeId" = {EVENT_TYPES['CONTRACT_INVOCATION_DAILY_COUNT']}
    and e."toId" in ({",".join(contract_ids)})
""")


get_current_high_low_value_users_for_list_of_contracts = lambda contract_ids: query(f"""
    select e."fromId" as user, case when (SUM(e."amount") >= 10) then 'high' else 'low' end as segment
    from event e
    where e."typeId" = {EVENT_TYPES['CONTRACT_INVOCATION_DAILY_COUNT']}
    and e."toId" in ({",".join(contract_ids)})
    and e."time" > now() - interval '30 days'
    group by e."fromId"
""")


get_high_frequency_users_for_list_of_contracts = lambda contract_ids: query(f"""
    select e."fromId" as user, case when (SUM(e."amount") >= 100) then 'high' else 'low' end as segment
    from event e
    where e."typeId" = {EVENT_TYPES['CONTRACT_INVOCATION_DAILY_COUNT']}
    and e."toId" in ({",".join(contract_ids)})
    and e."time" > now() - interval '7 days'
    group by e."fromId"
""")


get_new_and_retained_users_for_list_of_contracts = lambda contract_ids: query(f"""
    SELECT
        ue.user,
        CASE 
            WHEN ue.last_time <= now() - interval '90 days' THEN 'churned'
            WHEN ue.first_time > now() - interval '90 days' THEN 'new'
            WHEN ue.first_time <= now() - interval '90 days' AND ue.last_time > now() - interval '90 days' THEN 'retained'             
        END AS segment                                                                              
    FROM (
        SELECT
            e."fromId" AS user,
            MIN(e."time") AS first_time,
            MAX(e."time") AS last_time
        FROM
            event e
        WHERE
            e."typeId" = {EVENT_TYPES['CONTRACT_INVOCATION_DAILY_COUNT']}
            AND e."toId" IN ({",".join(contract_ids)})
        GROUP BY
            e."fromId"
        ) AS ue
""")


get_transaction_count_for_list_of_users_and_contracts = lambda user_ids, contract_ids: query(f"""
    select sum(e."amount") as count
    from event e
    where e."typeId" = {EVENT_TYPES['CONTRACT_INVOCATION_DAILY_COUNT']}
    and e."toId" in ({",".join(contract_ids)})  
    and e."fromId" in ({",".join(user_ids)})
""")


get_recent_transaction_count_for_list_of_users_and_contracts = lambda user_ids, contract_ids: query(f"""
    select sum(e."amount") as count
    from event e
    where e."typeId" = {EVENT_TYPES['CONTRACT_INVOCATION_DAILY_COUNT']}
    and e."toId" in ({",".join(contract_ids)})  
    and e."fromId" in ({",".join(user_ids)})
    and e."time" > now() - interval '7 days'
""")


get_high_value_users_for_collection = lambda collection_slug: query(f"""
    SELECT
        e."fromId" AS user,
        COUNT(DISTINCT paa."projectId") AS project_count,
        SUM(e."amount") AS transaction_count
    FROM
        event e
    INNER JOIN
        project_artifacts_artifact paa ON paa."artifactId" = e."toId"
    INNER JOIN
        project p ON p.id = paa."projectId"
    WHERE
        e."typeId" = {EVENT_TYPES['CONTRACT_INVOCATION_DAILY_COUNT']}
        AND e."toId" IN (
            SELECT a.id
            FROM artifact a
            WHERE a.type IN ('CONTRACT_ADDRESS', 'FACTORY_ADDRESS')
            AND a.namespace = 'OPTIMISM'
            AND a.id IN (
                SELECT a.id
                FROM collection_projects_project cpp
                INNER JOIN collection c ON c.id = cpp."collectionId"
                WHERE c.slug = '{collection_slug}'
            )
        )
    GROUP BY
        e."fromId"
    HAVING
        COUNT(DISTINCT paa."projectId") >= 3
        AND SUM(e."amount") >= 10;
""")


def test_lambdas(slug):

    print()
    project_id = get_project_id_from_slug(slug)
    print(f"Project ID: {project_id}")

    contracts = get_contracts_that_belong_to_project(project_id)    
    contract_ids = [str(contract['id']) for contract in contracts]
    print(f"Found {len(contracts)} contracts deployed and in use.")

    lifetime_users = get_lifetime_users_for_list_of_contracts(contract_ids)
    print(f"Lifetime user base: {len(lifetime_users)} users.")

    active_users = get_current_high_low_value_users_for_list_of_contracts(contract_ids)
    high_value_users = [user['user'] for user in active_users if user['segment'] == 'high']
    high_value_user_ids = [str(user) for user in high_value_users]
    low_value_users = [user['user'] for user in active_users if user['segment'] == 'low']
    print(f"Monthly active users: {len(active_users)} users, {len(high_value_users)} high value, {len(low_value_users)} low value.")
    print(f"Inactive users: {len(lifetime_users) - len(active_users)} users.")

    high_frequency_users = get_high_frequency_users_for_list_of_contracts(contract_ids)
    high_frequency_users = [user['user'] for user in high_frequency_users if user['segment'] == 'high']
    high_frequency_user_ids = [str(user) for user in high_frequency_users]
    print(f"High frequency users: {len(high_frequency_users)} users.")

    transactions = get_transactions_for_list_of_contracts(contract_ids)
    num_transactions = get_transaction_count_for_list_of_contracts(contract_ids)[0]['count']
    print(f"Count: {num_transactions} transactions with those contracts.")
    
    num_recent_transactions = get_recent_transaction_count_for_list_of_contracts(contract_ids)[0]['count']
    print(f"Count: {num_recent_transactions} transactions with those contracts in the last 7 days.")
    
    transaction_fees = get_transaction_fees_for_list_of_contracts(contract_ids)
    fees = sum([transaction['amount'] for transaction in transaction_fees])
    fees = get_transaction_fee_sum_for_list_of_contracts(contract_ids)[0]['fees']
    fees = wei_to_eth(fees)
    print(f"Total fees: {fees} ETH for all transactions.")

    avg_fee = get_avg_transaction_fee_for_list_of_contracts(contract_ids)[0]['fees']
    avg_fee = wei_to_eth(avg_fee)
    print(f"Average fee: {avg_fee} ETH per transaction. (Check: {fees / num_transactions})")

    new_and_retained_users = get_new_and_retained_users_for_list_of_contracts(contract_ids)
    new_users = [user['user'] for user in new_and_retained_users if user['segment'] == 'new']
    retained_users = [user['user'] for user in new_and_retained_users if user['segment'] == 'retained']
    churned_users = [user['user'] for user in new_and_retained_users if user['segment'] == 'churned']
    print(f"New users: {len(new_users)} users. Retained users: {len(retained_users)} users. Churned users: {len(churned_users)} users.")
    print(f"Churn rate: {len(churned_users) / len(new_and_retained_users)}")

    high_value_ecosystem_users = get_high_value_users_for_collection('optimism')
    print(f"Found {len(high_value_ecosystem_users)} high value ecosystem users.")

    lus = set([user['user'] for user in lifetime_users])
    eus = set([user['user'] for user in high_value_ecosystem_users])
    high_value_users_who_use_this_app = lus.intersection(eus)
    print(f"Users who are also high value ecosystem users: {len(high_value_users_who_use_this_app)}.")


def oso_metrics(slug, network):

    slug = slug.lower()
    network = network.upper()
    
    print(f"Querying developer metrics for project `{slug}` on Github...")

    start_time = time.time()
    result = execute_saved_query("github_metrics_by_project", params=[slug], col_names=True)
    end_time = time.time()
    print("\nReturning results:")
    for k,v in zip(result[0], result[1]):
        time.sleep(.25)
        print(f"{k}: {v}")
    print(f"\nQuery took {end_time - start_time} seconds.")

    print(f"\nQuerying onchain metrics for project `{slug}` on {network}...")

    start_time = time.time()
    result = execute_saved_query("onchain_metrics_by_project", params=[slug, network], col_names=True)
    end_time = time.time()    
    print("\nReturning results:")
    for k,v in zip(result[0], result[1]):
        time.sleep(.25)
        if 'fee' in k:
            print(f"{k}: {wei_to_eth(v)} ETH")
        else:
            print(f"{k}: {v}")
    print(f"\nQuery took {end_time - start_time} seconds.")

    print()
        

def oso_demo():
    while True:
        slug = input("Enter the slug for a project building on Optimism: ")
        network = "OPTIMISM"
        oso_metrics(slug, network)
        print()
        status = input("Enter 'q' to quit, or any other key to continue: ")
        if status == 'q':
            break


def test():
    oso_metrics('ethereum-attestation-service', 'optimism')
    test_lambdas('ethereum-attestation-service')
    

test()