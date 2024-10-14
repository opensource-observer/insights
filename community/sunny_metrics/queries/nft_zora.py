from config import DATE_START, DATE_END, X, Y


def dune_creator_contracts(wallet_address):
    return f"""
        SELECT COUNT(DISTINCT address)
        FROM zora.contracts
         WHERE "from" = '{wallet_address}'
        AND created_at BETWEEN CAST('{DATE_START}' AS TIMESTAMP) AND CAST('{DATE_END}' AS TIMESTAMP);
    
    """


# def artnft_ndrops(blockchain: str, contract_address: str) -> str:
#     return f"""
#     WITH nft_contracts AS (
#         SELECT DISTINCT nft_address
#         FROM {blockchain}.nft.ez_nft_transfers
#         WHERE block_timestamp BETWEEN '{DATE_START}' AND '{DATE_END}'
#     )
#     SELECT 
#         COUNT(*) AS number_of_drops
#     FROM nft_contracts nc
#     JOIN {blockchain}.core.dim_contracts dc ON nc.nft_address = dc.address
#     WHERE dc.created_block_timestamp BETWEEN '{DATE_START}' AND '{DATE_END}';
#     """

def artnft_nam(wallet_address):
    return f"""

        WITH creator_contracts AS (
          SELECT
            address AS nft_address
          FROM zora.contracts
          WHERE
            "from" = FROM_BASE58('{wallet_address}')
            AND created_at BETWEEN TRY_CAST('{DATE_START}' AS TIMESTAMP) AND TRY_CAST('{DATE_END}' AS TIMESTAMP)
        )
        SELECT
          COUNT(DISTINCT buyer) AS active_minters
        FROM nft.trades
        WHERE
          nft_contract_address IN (
            SELECT
              nft_address
            FROM creator_contracts
          )
          AND blockchain = 'zora'
          AND evt_Type = 'Mint'
          AND block_time BETWEEN TRY_CAST('{DATE_START}' AS TIMESTAMP) AND TRY_CAST('{DATE_END}' AS TIMESTAMP)
          
     """