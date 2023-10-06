WITH EventData AS (
    SELECT
        p."slug" AS project_slug,
        p."name" AS project_name,
        e."id" AS event_id,
        e."fromId" AS contributor_id,
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
        collection_projects_project cpp ON p."id" = cpp."projectId"
    JOIN
        collection c ON cpp."collectionId" = c."id"
    JOIN (
        SELECT
            a."id" AS artifact_id,
            MIN(e."time") AS first_star_time
        FROM
            artifact a
        LEFT JOIN
            event e ON a."id" = e."toId" AND e."type" = 'STARRED'
        WHERE
            e."time" IS NOT NULL
        GROUP BY
            a."id"
    ) fse ON a."id" = fse.artifact_id
    WHERE
        e."time" >= %s -- start date parameter
        AND e."type" IN (
            'COMMIT_CODE',
            'PULL_REQUEST_CREATED',
            'PULL_REQUEST_MERGED',
            'PULL_REQUEST_CLOSED',
            'PULL_REQUEST_APPROVED',
            'ISSUE_CLOSED',
            'ISSUE_CREATED'
        )
        AND c."slug" = %s  --collection slug parameter
        AND e."time" > fse.first_star_time -- Filter events after the first star event
)
SELECT
    project_slug,    
    month_year,
    contributor_id,
    event_type,
    COUNT(*) AS num_contributions
FROM
    EventData
GROUP BY
    project_slug,
    month_year,
    contributor_id,
    event_type
ORDER BY
    project_slug,
    month_year,
    contributor_id;
