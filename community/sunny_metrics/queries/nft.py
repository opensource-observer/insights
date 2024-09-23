from config import DATE_START, DATE_END, X, Y


def creator_contracts(blockchain: str, wallet_address: str) -> str:
    return f"""
    SELECT address AS nft_address
    FROM {blockchain}.core.dim_contracts
    WHERE creator_address = '{wallet_address}'
    AND created_block_timestamp BETWEEN '{DATE_START}' AND '{DATE_END}';
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

def artnft_nam(blockchain: str, wallet_address: str) -> str:
    return f"""
    WITH creator_contracts AS (
        SELECT address AS nft_address
        FROM {blockchain}.core.dim_contracts
        WHERE creator_address = '{wallet_address}'
        AND created_block_timestamp BETWEEN '{DATE_START}' AND '{DATE_END}'
    )
    SELECT COUNT(DISTINCT nft_to_address) AS active_minters
    FROM {blockchain}.nft.ez_nft_transfers
    WHERE nft_address IN (SELECT nft_address FROM creator_contracts)
    AND nft_from_address = nft_address
    AND block_timestamp BETWEEN '{DATE_START}' AND '{DATE_END}';
    """
