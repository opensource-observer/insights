from config import DATE_START, DATE_END, X, Y

def artmarketplace_nac(blockchain: str, contract_address: str) -> str:
    return f"""
    WITH nft_contracts AS (
        SELECT DISTINCT nft_address
        FROM {blockchain}.nft.ez_nft_transfers
        WHERE platform_address = '{contract_address}'
        AND block_timestamp BETWEEN '{DATE_START}' AND '{DATE_END}'
    )
    SELECT 
        COUNT(DISTINCT dc.creator_address)
    FROM nft_contracts nc
    JOIN {blockchain}.core.dim_contracts dc ON nc.nft_address = dc.address
    WHERE dc.created_block_timestamp BETWEEN '{DATE_START}' AND '{DATE_END}';
    """

def artmarketplace_nam(blockchain: str, contract_address: str) -> str:
    return f"""
    SELECT COUNT(DISTINCT nft_to_address) AS active_minters
    FROM {blockchain}.nft.ez_nft_transfers
    WHERE platform_address = '{contract_address}'
    AND nft_from_address = nft_address
    AND block_timestamp BETWEEN '{DATE_START}' AND '{DATE_END}';
    """

def artmarketplace_ntrxns(blockchain: str, contract_address: str) -> str:
    return f"""
    SELECT COUNT(*) AS marketplace_transactions
    FROM {blockchain}.nft.ez_nft_sales
    WHERE platform_address = '{contract_address}'
    AND block_timestamp BETWEEN '{DATE_START}' AND '{DATE_END}';
    """

def artmarketplace_valtrxns(blockchain: str, contract_address: str) -> str:
    return f"""
    WITH hourly_eth_prices AS (
        SELECT hour, price AS eth_price
        FROM {blockchain}.price.ez_prices_hourly
        WHERE symbol = 'ETH'
            AND hour BETWEEN '{DATE_START}' AND '{DATE_END}'
        ),
        nftmarketplace_transactions AS(
            SELECT block_timestamp, total_fees_usd
            FROM {blockchain}.nft.ez_nft_sales
            WHERE platform_address = '{contract_address}'
            AND block_timestamp BETWEEN '{DATE_START}' AND '{DATE_END}'
        ),
        transactions_with_prices AS (
            SELECT 
                b.block_timestamp,
                b.total_fees_usd,
                h.eth_price,
                b.total_fees_usd / h.eth_price AS eth_value
            FROM nftmarketplace_transactions b
            JOIN hourly_eth_prices h ON DATE_TRUNC('hour', b.block_timestamp) = h.hour
        )
    SELECT SUM(eth_value) AS total_eth_value
    FROM transactions_with_prices;
    """