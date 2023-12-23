SELECT 
    p.slug AS slug,
    -- GITHUB STATS
    COUNT(DISTINCT CASE WHEN a."type" = 'GIT_REPOSITORY' THEN a."id" END) AS count_repos,
    MIN(CASE WHEN e."typeId" = 2 THEN e."time" END) AS first_PR,
    MIN(CASE WHEN e."typeId" = 4 THEN e."time" END) AS first_commit,
    MIN(CASE WHEN e."typeId" = 9 AND e."amount" > 0 THEN e."time" END) AS first_download,
    MAX(CASE WHEN e."typeId" = 14 THEN e."amount" END) AS total_stars,
    MAX(CASE WHEN e."typeId" = 22 THEN e."amount" END) AS total_forks,
    COUNT(DISTINCT CASE WHEN e."typeId" IN (2,4,18) THEN e."fromId" END) AS total_contributors,
    COUNT(DISTINCT CASE WHEN e."typeId" IN (2,4,18) AND e."time" >= NOW() - INTERVAL '180 days' THEN e."fromId" END) AS contributors_last_180_days,
    -- ONCHAIN STATS
    COUNT(DISTINCT CASE WHEN a."type" IN ('CONTRACT_ADDRESS', 'FACTORY_ADDRESS') AND a.namespace = 'OPTIMISM' THEN a."id" END) AS count_contracts,
    MIN(CASE WHEN e."typeId" = 25 THEN e."time" END) AS first_txn,
    COUNT(DISTINCT CASE WHEN e."typeId" = 25 THEN e."fromId" END) AS total_users,
    COUNT(DISTINCT CASE WHEN e."typeId" = 25 AND e."time" >= NOW() - INTERVAL '180 days' THEN e."fromId" END) AS users_last_180_days,        
    SUM(CASE WHEN e."typeId" = 25 THEN e."amount"  END) AS total_txns,
    SUM(CASE WHEN e."typeId" = 25 AND e."time" >= NOW() - INTERVAL '180 days' THEN e."amount" END) AS txns_last_180_days,
    SUM(CASE WHEN e."typeId" = 26 THEN e."amount" / 10e18 END) AS total_fees,
    SUM(CASE WHEN e."typeId" = 26 AND e."time" >= NOW() - INTERVAL '180 days' THEN e."amount" / 10e18 END) AS fees_last_180_days,
    -- NPM STATS
    COUNT(DISTINCT CASE WHEN a."type" = 'NPM_PACKAGE' THEN a."id" END) AS count_npm,
    SUM(CASE WHEN e."typeId" = 9 THEN e."amount" END) AS total_downloads,
    SUM(CASE WHEN e."typeId" = 9 AND e."time" >= NOW() - INTERVAL '180 days' THEN e."amount" END) AS downloads_last_180_days
FROM project p
JOIN project_artifacts_artifact paa ON p."id" = paa."projectId"
LEFT JOIN artifact a ON paa."artifactId" = a."id"
LEFT JOIN event e ON e."toId" = paa."artifactId" 
WHERE p.slug = %s -- slug parameter
GROUP BY p.slug;