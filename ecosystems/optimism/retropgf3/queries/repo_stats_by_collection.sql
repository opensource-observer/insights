WITH EventData AS (
    SELECT
        p."slug" AS project_slug,
        p."name" AS project_name,
        a."name" AS artifact_name,
        e."fromId" AS contributor_id,
        e."id" AS event_id,   
        e."type" AS event_type,     
        e."time" as event_time
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
    WHERE
        a."namespace" = 'GITHUB'
        AND c."slug" = %s --collection slug parameter
)

SELECT
    project_slug,    
    project_name,
    artifact_name,
    COUNT(DISTINCT CASE WHEN event_type = 'STARRED' THEN contributor_id END) AS stars_count,
    COUNT(DISTINCT CASE WHEN event_type = 'FORKED' THEN contributor_id END) AS forks_count,
    COUNT(DISTINCT CASE WHEN event_type IN ('COMMIT_CODE', 'PULL_REQUEST_MERGED') THEN contributor_id END) AS num_developers,
    MIN(event_time) AS first_date,
    MAX(event_time) AS last_date
FROM
    EventData
GROUP BY
    project_slug,
    project_name,
    artifact_name
ORDER BY
    project_slug;