from config import DATE_START, DATE_END, X, Y

def zora_artmarketplace_nac(contract_address) -> str:
    return f"""
        WITH nft_contracts AS (
            SELECT DISTINCT nft_contract_address
            FROM nft.trades
            WHERE blockchain = 'zora'  
            AND aggregator_address = '{contract_address}'  
            AND block_time BETWEEN TRY_CAST('{DATE_START}' AS TIMESTAMP) AND TRY_CAST('{DATE_END}' AS TIMESTAMP)
        )
        SELECT
            COUNT(DISTINCT c."from") AS active_creators
        FROM zora.contracts c
        JOIN nft_contracts nc ON c.nft_contract_address = nc.nft_contract_address;
    """

#assumption that 'executed_by' is marketplace_address in case of marketplace and wallet address in case of creator
def zora_artmarketplace_nam(contract_address) -> str:
    return f"""
            
        SELECT
          COUNT(DISTINCT buyer) AS active_minters
        FROM nft.trades
        WHERE
          AND blockchain = 'zora'
          AND evt_Type = 'Mint'
          AND block_time BETWEEN TRY_CAST('{DATE_START}' AS TIMESTAMP) AND TRY_CAST('{DATE_END}' AS TIMESTAMP)
          AND aggregator_address = {contract_address}

    """

#assumption that 'executed_by' is marketplace_address in case of marketplace and wallet address in case of creator
def zora_artmarketplace_ntrxns(contract_address) -> str:
    return f"""
    SELECT COUNT(*) AS marketplace_transactions
    FROM nft.transfers
    WHERE blockchain = 'zora'
    AND block_time BETWEEN TRY_CAST('{DATE_START}' AS TIMESTAMP) AND TRY_CAST('{DATE_END}' AS TIMESTAMP)
    AND aggregator_address = {contract_address};
    """


def zora_artmarketplace_valtrxns(contract_address) -> str:
    return f"""
        WITH hourly_eth_prices AS (
            SELECT 
                date_trunc('hour', minute) AS hour, 
                AVG(price::double / 1e18) AS eth_price 
            FROM prices.usd
            WHERE symbol = 'ETH'
                AND blockchain = 'ethereum'
                AND minute BETWEEN TRY_CAST('{DATE_START}' AS TIMESTAMP) AND TRY_CAST('{DATE_END}' AS TIMESTAMP)
            GROUP BY date_trunc('hour', minute)
        ),
        nftmarketplace_transactions AS (
            SELECT 
                block_time,
                amount_usd
            FROM nft.trades
            WHERE blockchain = 'zora' 
                AND aggregator_address = {contract_address}
                AND block_time BETWEEN TRY_CAST('{DATE_START}' AS TIMESTAMP) AND TRY_CAST('{DATE_END}' AS TIMESTAMP)
        ),
        transactions_with_prices AS (
            SELECT 
                n.block_time,
                n.amount_usd,
                h.eth_price,
                n.amount_usd / h.eth_price AS eth_value
            FROM nftmarketplace_transactions n
            JOIN hourly_eth_prices h ON date_trunc('hour', n.block_time) = h.hour
        )
        SELECT SUM(eth_value) AS total_eth_value
        FROM transactions_with_prices;
        """