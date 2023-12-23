WITH EventData AS (
    SELECT
        p."slug" AS project_slug,
        p."name" AS project_name,
        a."name" AS artifact_name,
        e."fromId" AS contributor_id,
        e."id" AS event_id,   
        e."typeId" AS event_type,     
        e."time" as event_time
    FROM
        project p
    JOIN
        project_artifacts_artifact paa ON p."id" = paa."projectId"
    JOIN
        artifact a ON paa."artifactId" = a."id"
    JOIN
        event e ON a."id" = e."toId"
    WHERE
        a."namespace" = 'GITHUB'
        AND p.slug =  %s --project slug parameter
)

SELECT
    project_slug,    
    COUNT(DISTINCT artifact_name) AS repo_count,
    COUNT(DISTINCT CASE WHEN event_type = 21 THEN contributor_id END) AS stars_count,
    COUNT(DISTINCT CASE WHEN event_type = 23 THEN contributor_id END) AS forks_count,
    COUNT(DISTINCT CASE WHEN event_type = 4 THEN contributor_id END) AS developers_count,
    COUNT(DISTINCT CASE WHEN event_type IN (3,6) THEN contributor_id END) AS maintainers_count,
    COUNT(DISTINCT CASE WHEN event_type IN (3,4,6,18) THEN contributor_id END) AS contributors_count,
    MIN(event_time) AS first_commit,
    MAX(event_time) AS most_recent_commit
FROM
    EventData
GROUP BY
    project_slug;
