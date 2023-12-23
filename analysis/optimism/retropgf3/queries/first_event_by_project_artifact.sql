SELECT
    p.id,
    p.slug,
    a.id,
    a.name,
    et.name,
    MIN(e.time) AS first_event_time
FROM event e
JOIN event_type et ON e."typeId" = et.id
JOIN artifact a ON e."toId" = a.id
JOIN project_artifacts_artifact paa ON a.id = paa."artifactId"
JOIN project p ON paa."projectId" = p.id
WHERE
    p."slug" = %s -- project slug parameter
GROUP BY
    p.id,
    p.slug,
    a.id,
    a.name,
    et.name;