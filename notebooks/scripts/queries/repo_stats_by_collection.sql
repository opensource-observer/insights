SELECT
    p."slug" AS project_slug,
    p."name" AS project_name,
    a."name" AS artifact_name,
    COUNT(DISTINCT e."id") AS stars_count,
    MIN(e."time") AS first_date,
    MAX(e."time") AS last_date
FROM
    project p
LEFT JOIN
    project_artifacts_artifact ON p."id" = project_artifacts_artifact."projectId"
LEFT JOIN
    artifact a ON project_artifacts_artifact."artifactId" = a."id"
LEFT JOIN
    event e ON a."id" = e."toId" AND e."type" = 'STARRED'
LEFT JOIN
    collection_projects_project cpp ON p."id" = cpp."projectId"
LEFT JOIN
    collection c ON cpp."collectionId" = c."id"
WHERE
    e."time" IS NOT NULL
    AND e."time" >= %s  -- Replace with your start date parameter
    AND c."slug" = %s  -- Replace with your collection slug parameter
GROUP BY
    p."slug",
    p."name",
    a."name";
