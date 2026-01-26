-- optimism.grants.grants_consolidated

SELECT
  funding_date,
  application_name,
  oso_project_slug,
  application_url,
  amount,
  'Retro Funding' AS grant_type,
  CASE
    WHEN retro_round < 7 THEN 'Retro Funding Round ' || retro_round::VARCHAR
    ELSE 'Retro Funding Season ' || retro_round::VARCHAR
  END AS grants_season_or_mission,
  round_type AS intent
FROM optimism.grants.retrofunding_consolidated
UNION ALL
SELECT
  grant_start_date AS funding_date,
  application_name,
  oso_project_slug,
  application_url,
  op_total_amount AS amount,
  'Gov Fund' AS grant_type,
  grants_season_or_mission,
  intent
FROM optimism.grants.govfund_consolidated