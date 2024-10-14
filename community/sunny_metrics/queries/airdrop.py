from config import DATE_START, DATE_END, X, Y

#get the number of active users on given chain
def airdrop_nusers(blockchain, contract_address):
    
    return f"""
           WITH user_transactions AS (
                SELECT 
                    t.from_address,
                    t.block_timestamp,
                    COUNT(*) OVER (
                        PARTITION BY t.from_address 
                        ORDER BY t.block_timestamp 
                        RANGE BETWEEN INTERVAL '{Y} DAY' PRECEDING AND CURRENT ROW
                    ) AS tx_count_last_Y_days
                FROM {blockchain}.core.fact_transactions t
                WHERE t.to_address = '{contract_address}'
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


#get the value of total transactions in eth. 
def airdrop_sumtrxns(blockchain, contract_address):
    
    return f"""
            SELECT SUM(value) AS total_eth_value
            FROM {blockchain}.core.fact_transactions
            WHERE to_address = '{contract_address}'
            AND block_timestamp BETWEEN '{DATE_START}' AND '{DATE_END}'
    """
