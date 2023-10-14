WITH EventData AS (
    SELECT
        p."slug" AS project_slug,
        p."name" AS project_name,
        e."id" AS event_id,
        a2."name" AS contributor_name,
        e."type" AS event_type,
        TO_CHAR(e."time", 'YYYY-MM') AS month_year
    FROM
        project p
    JOIN
        project_artifacts_artifact paa ON p."id" = paa."projectId"
    JOIN
        artifact a ON paa."artifactId" = a."id"
    JOIN
        event e ON a."id" = e."toId"
    JOIN
        artifact a2 ON e."fromId" = a2."id"        
    JOIN
        collection_projects_project cpp ON p."id" = cpp."projectId"
    JOIN
        collection c ON cpp."collectionId" = c."id"
    WHERE
        e."type" IN (
            'COMMIT_CODE',
            'PULL_REQUEST_CREATED',
            'PULL_REQUEST_MERGED',
            'PULL_REQUEST_CLOSED',
            'PULL_REQUEST_APPROVED',
            'ISSUE_CLOSED',
            'ISSUE_CREATED'
        )
)
SELECT
    project_slug,    
    month_year,
    contributor_name,
    event_type,
    COUNT(*) AS num_contributions
FROM
    EventData
GROUP BY
    project_slug,
    month_year,
    contributor_name,
    event_type
ORDER BY
    project_slug,
    month_year,
    contributor_name;
