SELECT
    p."slug" AS project_slug,
    p."name" AS project_name,
    a1."name" AS artifact_name,
    a2."name" AS contributor_name,
    e."time" AS event_time,
    e."type" AS event_type
FROM
    project p
JOIN
    project_artifacts_artifact paa ON p."id" = paa."projectId"
JOIN
    artifact a1 ON paa."artifactId" = a1."id"
JOIN
    event e ON a1."id" = e."toId"
JOIN
    artifact a2 ON e."fromId" = a2."id"
WHERE 
    p."slug" = %s -- project slug parameter
    AND a1."namespace" = %s -- artifact namespace parameter