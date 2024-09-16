from config import DATE_START, DATE_END, X, Y

def rwa_nusers(blockchain: str, contract_address: str) -> str:
    return f"""
    WITH contract_addresses AS (
        SELECT DISTINCT address
        FROM {blockchain}.core.dim_contracts
        WHERE created_block_timestamp BETWEEN '{DATE_START}' AND '{DATE_END}'
    ),
    user_transactions AS (
        SELECT 
            t.from_address,
            t.block_timestamp,
            COUNT(*) OVER (
                PARTITION BY t.from_address 
                ORDER BY t.block_timestamp 
                RANGE BETWEEN INTERVAL {Y} DAY PRECEDING AND CURRENT ROW
            ) AS tx_count_last_Y_days
        FROM {blockchain}.core.fact_transactions t
        LEFT JOIN contract_addresses c ON t.from_address = c.address
        WHERE t.to_address = '{contract_address}'
        AND t.block_timestamp BETWEEN '{DATE_START}' AND '{DATE_END}'
        AND c.address IS NULL
    ),
    active_users AS (
        SELECT DISTINCT from_address
        FROM user_transactions
        WHERE tx_count_last_Y_days >= {X}
    )
    SELECT COUNT(*) AS active_users
    FROM active_users;
    """

def rwa_ntrxns(blockchain: str, contract_address: str) -> str:
    return f"""
    SELECT COUNT(*) AS total_transactions
    FROM {blockchain}.core.fact_transactions
    WHERE to_address = '{contract_address}'
    AND block_timestamp BETWEEN '{DATE_START}' AND '{DATE_END}';
    """

def rwa_sumtrxns(blockchain: str, contract_address: str) -> str:
    return f"""
    SELECT SUM(value) AS total_eth_value
    FROM {blockchain}.core.fact_transactions
    WHERE to_address = '{contract_address}'
    AND block_timestamp BETWEEN '{DATE_START}' AND '{DATE_END}';
    """
