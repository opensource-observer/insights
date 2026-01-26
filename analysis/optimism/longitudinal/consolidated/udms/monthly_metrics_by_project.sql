-- optimism.grants.monthly_metrics_by_project

WITH projects AS (
  SELECT DISTINCT
    pc.oso_project_id,
    p.display_name AS project_name
  FROM optimism.grants.projects_catalog pc
  JOIN oso.projects_v1 p
    ON pc.oso_project_id=p.project_id
),
base_metrics AS (
  SELECT
    tm.sample_date,
    tm.project_id,
    p.project_name,
    m.metric_event_source_category AS metric_source,
    m.metric_category,
    m.metric_name,
    tm.amount::DOUBLE AS amount
  FROM oso.timeseries_metrics_by_project_v0 tm
  JOIN projects p
    ON tm.project_id=p.oso_project_id
  JOIN optimism.grants.metrics_catalog m
    ON tm.metric_id=m.metric_id
),
transformed_metrics AS (
  SELECT
    sample_date,
    project_id,
    project_name,
    metric_source,
    metric_category,
    metric_name,
    CASE
      WHEN metric_name IN ('Gas Fees (Top Level)','Gas Fees (Trace Level, Amortized)') THEN amount/1e18
      ELSE amount
    END AS amount
  FROM base_metrics
  WHERE
    metric_source!='Other'
    AND NOT (
      metric_source='Celo'
      AND metric_name IN ('Gas Fees (Top Level)','Gas Fees (Trace Level, Amortized)')
    )
),
revenue_metrics AS (
  SELECT
    sample_date,
    project_id,
    project_name,
    metric_source,
    'Superchain Economic' AS metric_category,
    CASE
      WHEN metric_name='Gas Fees (Top Level)' THEN 'Revenue (Top Level)'
      WHEN metric_name='Gas Fees (Trace Level, Amortized)' THEN 'Revenue (Trace Level)'
    END AS metric_name,
    amount*CASE WHEN metric_source='OP Mainnet' THEN 1.0 ELSE 0.15 END AS amount
  FROM transformed_metrics
  WHERE metric_name IN ('Gas Fees (Top Level)','Gas Fees (Trace Level, Amortized)')
),
tvl_share AS (
  SELECT
    sample_date,
    project_id,
    project_name,
    'Superchain' AS metric_source,
    'DefiLlama' AS metric_category,
    'Superchain TVL Share' AS metric_name,
    CASE
      WHEN sum(amount)=0 THEN NULL
      ELSE sum(CASE WHEN metric_source!='Other' THEN amount ELSE 0 END)/sum(amount)
    END AS amount
  FROM base_metrics
  WHERE metric_category='DefiLlama' AND metric_name='TVL'
  GROUP BY 1,2,3
),
tvl_inflows AS (
  SELECT
    sample_date,
    project_id,
    project_name,
    metric_source,
    'DefiLlama' AS metric_category,
    'TVL Inflows' AS metric_name,
    amount-lag(amount) OVER (
      PARTITION BY project_id,metric_source
      ORDER BY sample_date
    ) AS amount
  FROM transformed_metrics
  WHERE metric_category='DefiLlama' AND metric_name='TVL'
),
unioned_metrics AS (
  SELECT * FROM transformed_metrics
  UNION ALL
  SELECT * FROM revenue_metrics
  UNION ALL
  SELECT * FROM tvl_share
  UNION ALL
  SELECT * FROM tvl_inflows
)
SELECT
  sample_date,
  project_id,
  project_name,
  metric_source,
  metric_category,
  metric_name,
  amount
FROM unioned_metrics