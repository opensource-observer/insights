from config import DATE_START, DATE_END, X, Y

def lending_nproviders(blockchain: str, contract_address: str) -> str:
    return f"""
    SELECT COUNT(DISTINCT depositor) AS unique_collateral_providers
    FROM {blockchain}.defi.ez_lending_deposits
    WHERE contract_address = '{contract_address}'
    AND block_timestamp BETWEEN '{DATE_START}' AND '{DATE_END}';
    """

def lending_nborrowers(blockchain: str, contract_address: str) -> str:
    return f"""
    SELECT COUNT(DISTINCT borrower) AS active_borrowers
    FROM {blockchain}.defi.ez_lending_borrows
    WHERE contract_address = '{contract_address}'
    AND block_timestamp BETWEEN '{DATE_START}' AND '{DATE_END}';
    """

def lending_ntrxns(blockchain: str, contract_address: str) -> str:
    return f"""
    SELECT 
        (SELECT COUNT(*) FROM {blockchain}.defi.ez_lending_deposits WHERE contract_address = '{contract_address}'
        AND block_timestamp BETWEEN '{DATE_START}' AND '{DATE_END}') +
        (SELECT COUNT(*) FROM {blockchain}.defi.ez_lending_borrows WHERE contract_address = '{contract_address}'
        AND block_timestamp BETWEEN '{DATE_START}' AND '{DATE_END}') +
        (SELECT COUNT(*) FROM {blockchain}.defi.ez_lending_repayments WHERE contract_address = '{contract_address}'
        AND block_timestamp BETWEEN '{DATE_START}' AND '{DATE_END}') +
        (SELECT COUNT(*) FROM {blockchain}.defi.ez_lending_withdraws WHERE contract_address = '{contract_address}'
        AND block_timestamp BETWEEN '{DATE_START}' AND '{DATE_END}') +
        (SELECT COUNT(*) FROM {blockchain}.defi.ez_lending_liquidations WHERE contract_address = '{contract_address}'
        AND block_timestamp BETWEEN '{DATE_START}' AND '{DATE_END}') +
        (SELECT COUNT(*) FROM {blockchain}.defi.ez_lending_flashloans WHERE contract_address = '{contract_address}'
        AND block_timestamp BETWEEN '{DATE_START}' AND '{DATE_END}')
    AS total_transactions;
    """

def lending_valtrxns(blockchain: str, contract_address: str) -> str:
    return f"""
    WITH hourly_eth_prices AS (
        SELECT hour, price AS eth_price
        FROM {blockchain}.price.ez_prices_hourly
        WHERE symbol = 'ETH'
        AND hour BETWEEN '{DATE_START}' AND '{DATE_END}'
    ),
    lending_transactions AS (
        SELECT block_timestamp, amount_usd
        FROM (
            SELECT block_timestamp, amount_usd FROM {blockchain}.defi.ez_lending_deposits
            WHERE contract_address = '{contract_address}' AND block_timestamp BETWEEN '{DATE_START}' AND '{DATE_END}'
            UNION ALL
            SELECT block_timestamp, amount_usd FROM {blockchain}.defi.ez_lending_borrows 
            WHERE contract_address = '{contract_address}' AND block_timestamp BETWEEN '{DATE_START}' AND '{DATE_END}'
            UNION ALL
            SELECT block_timestamp, amount_usd FROM {blockchain}.defi.ez_lending_repayments
            WHERE contract_address = '{contract_address}' AND block_timestamp BETWEEN '{DATE_START}' AND '{DATE_END}'
            UNION ALL
            SELECT block_timestamp, amount_usd FROM {blockchain}.defi.ez_lending_withdraws
            WHERE contract_address = '{contract_address}' AND block_timestamp BETWEEN '{DATE_START}' AND '{DATE_END}'
            UNION ALL
            SELECT block_timestamp, amount_usd FROM {blockchain}.defi.ez_lending_liquidations
            WHERE contract_address = '{contract_address}' AND block_timestamp BETWEEN '{DATE_START}' AND '{DATE_END}'
            UNION ALL
            SELECT block_timestamp, flashloan_amount_usd AS amount_usd FROM {blockchain}.defi.ez_lending_flashloans
            WHERE contract_address = '{contract_address}' AND block_timestamp BETWEEN '{DATE_START}' AND '{DATE_END}'
        ) AS all_transactions
    ),
    transactions_with_prices AS (
        SELECT 
            l.block_timestamp,
            l.amount_usd,
            h.eth_price,
            l.amount_usd / h.eth_price AS eth_value
        FROM lending_transactions l
        JOIN hourly_eth_prices h ON DATE_TRUNC('hour', l.block_timestamp) = h.hour
    )
    SELECT 
        SUM(eth_value) AS total_eth_value
    FROM transactions_with_prices;
    """