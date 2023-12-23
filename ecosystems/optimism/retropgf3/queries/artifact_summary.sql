SELECT
    p.slug AS project,
    a.name AS artifact,
    SUM(CASE WHEN e."typeId" = 25 THEN e.amount ELSE 0 END) AS txns,
    SUM(CASE WHEN e."typeId" = 26 THEN e.amount ELSE 0 END) AS fees,
    MAX(CASE WHEN e."typeId" = 14 THEN e.amount ELSE 0 END) AS num_stars,
    MAX(CASE WHEN e."typeId" = 22 THEN e.amount ELSE 0 END) AS num_forks,
    MIN(CASE WHEN e."typeId" = 4 THEN e.time ELSE NULL END) AS first_commit,
    SUM(CASE WHEN e."typeId" = 4 THEN e.amount ELSE 0 END) AS sum_commits,
    SUM(CASE WHEN e."typeId" = 3 THEN e.amount ELSE 0 END) AS sum_prs_merged,
    SUM(CASE WHEN e."typeId" = 9 THEN e.amount ELSE 0 END) AS sum_downloads
FROM
    event e
LEFT JOIN
    project_artifacts_artifact paa ON e."toId" = paa."artifactId"
LEFT JOIN
    project p ON paa."projectId" = p."id"
LEFT JOIN
    artifact a ON paa."artifactId" = a."id"
WHERE
    p.slug IN (%s) -- list of project slugs parameter
    AND e."typeId" IN (3, 4, 9, 14, 22, 25, 26)
GROUP BY
    p.slug,
    a.name;