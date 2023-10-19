WITH Contracts AS (
    SELECT
        p.slug as project_slug,
        a.id AS contract_id,
        a.name AS contract_name,
        a.type AS contract_type,
        a.namespace AS contract_namespace
    FROM
        artifact a
    INNER JOIN
        project_artifacts_artifact paa ON paa."artifactId" = a.id
    INNER JOIN
        project p ON p.id = paa."projectId"
    WHERE
        p.slug =  %s --project slug parameter
        AND a.type IN ('CONTRACT_ADDRESS', 'FACTORY_ADDRESS')
        AND a.namespace = %s --network parameter (eg, OPTIMISM)
),
EventInfo AS (
    SELECT
        c.project_slug,
        e."toId" AS contract_id,
        SUM(CASE WHEN e."typeId" = 25 THEN e."amount" ELSE 0 END) AS transaction_count,
        SUM(CASE WHEN e."typeId" = 26 THEN e."amount" ELSE 0 END) AS fees
    FROM
        event e
    JOIN
        Contracts c ON e."toId" = c.contract_id
    WHERE
        e."typeId" IN (25, 26)
    GROUP BY
        c.project_slug, e."toId"
),
UserAnalysis AS (
    SELECT
        c.project_slug,
        e."fromId" AS user_id,
        SUM(CASE WHEN e."time" >= now() - interval '7 days' THEN e."amount" ELSE 0 END) AS txs_last_7,
        SUM(CASE WHEN e."time" >= now() - interval '30 days' THEN e."amount" ELSE 0 END) AS txs_last_30,
        SUM(CASE WHEN e."time" >= now() - interval '90 days' THEN e."amount" ELSE 0 END) AS txs_last_90,
        MIN(e."time") AS first_time,
        MAX(e."time") AS last_time
    FROM
        event e
    JOIN
        Contracts c ON e."toId" = c.contract_id
    WHERE
        e."typeId" = 25
    GROUP BY
        c.project_slug, e."fromId"
)
SELECT
    c.project_slug,
    
    COUNT(DISTINCT c.contract_id) AS contract_count,
    MAX(ei.transaction_count) AS transaction_count, -- TODO: fix this
    MAX(ei.fees) AS total_fees, -- TODO: fix this
    COALESCE(MAX(ei.fees) / NULLIF(MAX(ei.transaction_count), 0), 0) AS avg_fee_per_transaction, -- TODO: fix this
    
    COUNT(DISTINCT ua.user_id) AS total_users_count,
    COUNT(DISTINCT CASE WHEN ua.txs_last_7 >= 100 THEN ua.user_id END) AS high_frequency_users_count,
    
    COUNT(DISTINCT CASE WHEN ua.txs_last_7 >= 1 THEN ua.user_id END) AS weekly_active_users_count,
    COUNT(DISTINCT CASE WHEN ua.txs_last_30 >= 1 THEN ua.user_id END) AS monthly_active_users_count,
    COUNT(DISTINCT CASE WHEN ua.txs_last_90 >= 1 THEN ua.user_id END) AS quarterly_active_users_count,
    
    COUNT(DISTINCT CASE WHEN ua.txs_last_30 >= 10 THEN ua.user_id END) AS high_value_users_count,
    COUNT(DISTINCT CASE WHEN (ua.txs_last_30 >= 1 AND ua.txs_last_30 < 10) THEN ua.user_id END) AS low_value_users_count,
    
    COUNT(DISTINCT CASE WHEN ua.first_time > now() - interval '90 days' THEN ua.user_id END) AS new_user_count,
    COUNT(DISTINCT CASE WHEN ua.first_time <= now() - interval '90 days' AND ua.last_time > now() - interval '90 days' THEN ua.user_id END) AS retained_user_count,
    COUNT(DISTINCT CASE WHEN ua.last_time <= now() - interval '90 days' THEN ua.user_id END) AS churned_user_count
FROM
    Contracts c
LEFT JOIN
    EventInfo ei ON c.project_slug = ei.project_slug
LEFT JOIN
    UserAnalysis ua ON c.project_slug = ua.project_slug
GROUP BY
    c.project_slug;