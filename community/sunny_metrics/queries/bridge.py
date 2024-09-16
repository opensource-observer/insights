from config import DATE_START, DATE_END, X, Y

def bridge_nchains(blockchain: str, contract_address: str) -> str:
    return f"""
    SELECT COUNT(DISTINCT destination_chain) AS unique_chains
    FROM {blockchain}.defi.ez_bridge_activity
    WHERE bridge_address = '{contract_address}'
    AND block_timestamp BETWEEN '{DATE_START}' AND '{DATE_END}';
    """

def bridge_nusers(blockchain: str, contract_address: str) -> str:
    return f"""
    WITH contract_addresses AS (
        SELECT DISTINCT address
        FROM {blockchain}.core.dim_contracts
        WHERE created_block_timestamp BETWEEN '{DATE_START}' AND '{DATE_END}'
    ),
    user_transactions AS (
        SELECT 
            t.origin_from_address,
            t.block_timestamp,
            COUNT(*) OVER (
                PARTITION BY t.origin_from_address 
                ORDER BY t.block_timestamp 
                RANGE BETWEEN INTERVAL {Y} DAY PRECEDING AND CURRENT ROW
            ) AS tx_count_last_Y_days
        FROM {blockchain}.core.fact_transactions t
        LEFT JOIN contract_addresses c ON t.origin_from_address = c.address
        WHERE t.bridge_address = '{contract_address}'
        AND t.block_timestamp BETWEEN '{DATE_START}' AND '{DATE_END}'
    ),
    active_users AS (
        SELECT DISTINCT from_address
        FROM user_transactions
        WHERE tx_count_last_Y_days >= {X}
    )
    SELECT COUNT(*) AS active_users
    FROM active_users;
    """

def bridge_nbtrxns(blockchain: str, contract_address: str) -> str:
    return f"""
    SELECT COUNT(*) AS total_bridge_transactions
    FROM {blockchain}.defi.ez_bridge_activity
    WHERE bridge_address = '{contract_address}'
    AND block_timestamp BETWEEN '{DATE_START}' AND '{DATE_END}';
    """

def bridge_valtrxns(blockchain: str, contract_address: str) -> str:
    return f"""
    WITH hourly_eth_prices AS (
        SELECT hour, price AS eth_price
        FROM {blockchain}.price.ez_prices_hourly
        WHERE symbol = 'ETH'
        AND hour BETWEEN '{DATE_START}' AND '{DATE_END}'
    ),
    bridge_transactions AS(
        SELECT block_timestamp, amount_usd
        FROM {blockchain}.defi.ez_bridge_activity
        WHERE bridge_address = '{contract_address}'
        AND block_timestamp BETWEEN '{DATE_START}' AND '{DATE_END}'
    ),
    transactions_with_prices AS (
        SELECT 
            b.block_timestamp,
            b.amount_usd,
            h.eth_price,
            b.amount_usd / h.eth_price AS eth_value
        FROM bridge_transactions b
        JOIN hourly_eth_prices h ON DATE_TRUNC('hour', b.block_timestamp) = h.hour
    )
    SELECT 
        SUM(eth_value) AS total_eth_value
    FROM transactions_with_prices;
    """

def bridge_medianfee(blockchain: str, contract_address: str) -> str:
    return f"""
    WITH bridge_fees AS (
        SELECT 
            b.tx_hash,
            t.tx_fee AS eth_cost
        FROM {blockchain}.defi.ez_bridge_activity b
        JOIN {blockchain}.core.fact_transactions t ON b.tx_hash = t.tx_hash
        WHERE b.block_timestamp BETWEEN '{DATE_START}' AND '{DATE_END}'
        AND   b.bridge_address =  '{contract_address}'
    )
    SELECT 
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY eth_cost) AS median_eth_cost
    FROM bridge_fees;
    """
