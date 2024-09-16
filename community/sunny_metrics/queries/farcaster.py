from config import DATE_START, DATE_END, X, Y

def frames_nusers(name: str) -> str:
    return f"""
    WITH frame_fid AS (
      SELECT fid FROM fnames WHERE username = '{name}'
    ),
    frame_casts AS (
      SELECT hash, fid
      FROM casts
      WHERE fid = (SELECT fid FROM frame_fid)
        AND timestamp BETWEEN '{DATE_START}' AND '{DATE_END}'
    ),
    frame_reactions AS (
      SELECT fid, COUNT(*) as reaction_count
      FROM reactions
      WHERE target_cast_hash IN (SELECT hash FROM frame_casts)
        AND timestamp BETWEEN '{DATE_START}' AND '{DATE_END}'
      GROUP BY fid
    ),
    frame_replies AS (
      SELECT fid, COUNT(*) as reply_count
      FROM casts
      WHERE parent_hash IN (SELECT hash FROM frame_casts)
        AND timestamp BETWEEN '{DATE_START}' AND '{DATE_END}'
      GROUP BY fid
    ),
    total_engagements AS (
      SELECT COALESCE(r.fid, p.fid) as fid,
             COALESCE(r.reaction_count, 0) + COALESCE(p.reply_count, 0) as total_count
      FROM frame_reactions r
      FULL OUTER JOIN frame_replies p ON r.fid = p.fid
    )
    SELECT COUNT(*) as active_users
    FROM total_engagements
    WHERE total_count >= {X};
    """

def frames_interactions(name: str) -> str:
    return f"""
    WITH frame_fid AS (
      SELECT fid FROM fnames WHERE username = '{name}'
    ),
    frame_casts AS (
      SELECT hash, fid
      FROM casts
      WHERE fid = (SELECT fid FROM frame_fid)
        AND timestamp BETWEEN '{DATE_START}' AND '{DATE_END}'
    ),
    frame_reactions AS (
      SELECT fid, COUNT(*) as reaction_count
      FROM reactions
      WHERE target_cast_hash IN (SELECT hash FROM frame_casts)
        AND timestamp BETWEEN '{DATE_START}' AND '{DATE_END}'
      GROUP BY fid
    ),
    frame_replies AS (
      SELECT fid, COUNT(*) as reply_count
      FROM casts
      WHERE parent_hash IN (SELECT hash FROM frame_casts)
        AND timestamp BETWEEN '{DATE_START}' AND '{DATE_END}'
      GROUP BY fid
    ),
    total_engagements AS (
      SELECT COALESCE(r.fid, p.fid) as fid,
             COALESCE(r.reaction_count, 0) + COALESCE(p.reply_count, 0) as total_count
      FROM frame_reactions r
      FULL OUTER JOIN frame_replies p ON r.fid = p.fid
    )
    SELECT 
      (SELECT COUNT(*) FROM frame_casts) +
      (SELECT SUM(reaction_count) FROM frame_reactions) +
      (SELECT SUM(reply_count) FROM frame_replies) as total_transactions;
    """

def channel_nusers(channel_url: str) -> str:
    return f"""
    WITH channel_casts AS (
      SELECT hash, fid
      FROM casts
      WHERE root_parent_url = '{channel_url}'
        AND timestamp BETWEEN '{DATE_START}' AND '{DATE_END}'
    ),
    channel_reactions AS (
      SELECT fid, COUNT(*) as reaction_count
      FROM reactions
      WHERE target_cast_hash IN (SELECT hash FROM channel_casts)
        AND timestamp BETWEEN '{DATE_START}' AND '{DATE_END}'
      GROUP BY fid
    ),
    channel_replies AS (
      SELECT fid, COUNT(*) as reply_count
      FROM casts
      WHERE parent_hash IN (SELECT hash FROM channel_casts)
        AND timestamp BETWEEN '{DATE_START}' AND '{DATE_END}'
      GROUP BY fid
    ),
    total_engagements AS (
      SELECT COALESCE(r.fid, p.fid) as fid,
             COALESCE(r.reaction_count, 0) + COALESCE(p.reply_count, 0) as total_count
      FROM channel_reactions r
      FULL OUTER JOIN channel_replies p ON r.fid = p.fid
    )
    SELECT COUNT(*) as active_users
    FROM total_engagements
    WHERE total_count >= {X};
    """

def channel_interactions(channel_url: str) -> str:
    return f"""
    WITH channel_casts AS (
      SELECT hash, fid
      FROM casts
      WHERE root_parent_url = '{channel_url}'
        AND timestamp BETWEEN '{DATE_START}' AND '{DATE_END}'
    ),
    channel_reactions AS (
      SELECT fid, COUNT(*) as reaction_count
      FROM reactions
      WHERE target_cast_hash IN (SELECT hash FROM channel_casts)
        AND timestamp BETWEEN '{DATE_START}' AND '{DATE_END}'
      GROUP BY fid
    ),
    channel_replies AS (
      SELECT fid, COUNT(*) as reply_count
      FROM casts
      WHERE parent_hash IN (SELECT hash FROM channel_casts)
        AND timestamp BETWEEN '{DATE_START}' AND '{DATE_END}'
      GROUP BY fid
    ),
    total_engagements AS (
      SELECT COALESCE(r.fid, p.fid) as fid,
             COALESCE(r.reaction_count, 0) + COALESCE(p.reply_count, 0) as total_count
      FROM channel_reactions r
      FULL OUTER JOIN channel_replies p ON r.fid = p.fid
    )
    SELECT 
      (SELECT COUNT(*) FROM channel_casts) +
      (SELECT SUM(reaction_count) FROM channel_reactions) +
      (SELECT SUM(reply_count) FROM channel_replies) as total_transactions;
    """