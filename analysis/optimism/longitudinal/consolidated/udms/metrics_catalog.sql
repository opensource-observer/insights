-- optimism.grants.metrics_catalog

WITH chains AS (
  SELECT DISTINCT chain
  FROM oso.int_superchain_chain_names
  WHERE chain!='ETHEREUM'
),
metric_catalog AS (
  SELECT * FROM (
    VALUES
      ('DefiLlama','defillama_lp_fee','LP Fees'),
      ('DefiLlama','defillama_tvl','TVL'),

      ('Superchain Economic','contract_invocations','User Ops'),
      ('Superchain Economic','transactions','Transactions (Top Level)'),
      ('Superchain Economic','layer2_gas_fees','Gas Fees (Top Level)'),
      ('Superchain Economic','layer2_gas_fees_amortized','Gas Fees (Trace Level, Amortized)'),

      ('Superchain Users','active_addresses_aggregation','Active Addresses'),
      ('Superchain Users','worldchain_users_aggregation','World Users'),
      ('Superchain Users','farcaster_users','Farcaster Users'),

      ('Developer Activity','active_developers','Active Developers'),
      ('Developer Activity','contributors','Active Contributors'),

      ('Developer Activity','commits','Commits'),
      ('Developer Activity','forks','Forks'),
      ('Developer Activity','opened_issues','Issues Opened'),
      ('Developer Activity','closed_issues','Issues Closed'),
      ('Developer Activity','merged_pull_requests','PRs Merged'),
      ('Developer Activity','opened_pull_requests','PRs Opened'),
      ('Developer Activity','releases','Releases'),
      ('Developer Activity','stars','Stars'),

      ('Developer Lifecycle','active_full_time_contributor','Active Full Time Contributors'),
      ('Developer Lifecycle','active_part_time_contributor','Active Part Time Contributors'),
      ('Developer Lifecycle','first_time_contributor','First Time Contributors'),
      ('Developer Lifecycle','new_full_time_contributor','New Full Time Contributors'),
      ('Developer Lifecycle','new_part_time_contributor','New Part Time Contributors'),
      ('Developer Lifecycle','full_time_developers','Full Time Developers'),
      ('Developer Lifecycle','part_time_developers','Part Time Developers'),
      ('Developer Lifecycle','part_time_to_full_time_contributor','Part Time → Full Time Contributors'),
      ('Developer Lifecycle','full_time_to_part_time_contributor','Full Time → Part Time Contributors'),
      ('Developer Lifecycle','reactivated_full_time_contributor','Reactivated Full Time Contributors'),
      ('Developer Lifecycle','reactivated_part_time_contributor','Reactivated Part Time Contributors'),
      ('Developer Lifecycle','churned_after_first_time_contributor','Churned After First Time Contributors'),
      ('Developer Lifecycle','churned_after_part_time_contributor','Churned After Part Time Contributors'),
      ('Developer Lifecycle','churned_contributors','Churned Contributors')

  ) AS t(metric_category,metric_model,metric_name)
)
SELECT
  m.metric_id,
  c.metric_category,
  c.metric_name,
  CASE
    WHEN m.metric_event_source='OPTIMISM' THEN 'OP Mainnet'
    WHEN m.metric_event_source='GITHUB' THEN 'GitHub'
    WHEN sc.chain IS NOT NULL THEN initcap(lower(m.metric_event_source))
    ELSE 'Other'
  END AS metric_event_source_category,
  m.metric_event_source
FROM metrics_v0 AS m
JOIN metric_catalog AS c
  ON m.metric_model=c.metric_model
  AND m.metric_time_aggregation='monthly'
LEFT JOIN chains AS sc
  ON m.metric_event_source=sc.chain
WHERE NOT (m.metric_event_source='ETHEREUM' AND c.metric_category LIKE 'Superchain%')