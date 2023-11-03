WITH Devs AS (
    SELECT 
        p."id" AS "projectId",
        e."fromId" AS "fromId",
        TO_CHAR(DATE_TRUNC('MONTH', e."time"), 'YYYY-MM-01') AS "bucketMonthly",
        CASE 
            WHEN COUNT(DISTINCT CASE WHEN e."typeId" = 4 THEN e."time" END) >= 10 THEN 'FULL_TIME_DEV'
            WHEN COUNT(DISTINCT CASE WHEN e."typeId" = 4 THEN e."time" END) >= 1 THEN 'PART_TIME_DEV'
            ELSE 'OTHER_CONTRIBUTOR'
        END AS "devType",
        1 AS amount
    FROM 
        event e
    JOIN 
        project_artifacts_artifact paa ON e."toId" = paa."artifactId"
    JOIN 
        project p ON paa."projectId" = p.id
        
    WHERE
        e."typeId" IN (
            2, -- PULL_REQUEST_CREATED
            3, -- PULL_REQUEST_MERGED
            4, -- COMMIT_CODE
            6, -- ISSUE_CLOSED
            18 -- ISSUE_CREATED
        )
        -- AND e."toId" = 420126 -- uncomment for testing purposes
    GROUP BY
        p."id",
        e."fromId",
        TO_CHAR(DATE_TRUNC('MONTH', e."time"), 'YYYY-MM-01')
)
SELECT
    Devs."projectId",
    Devs."devType",
    Devs."bucketMonthly",
    SUM(Devs."amount") AS "amount"
FROM 
    Devs
GROUP BY
    Devs."projectId",
    Devs."devType",
    Devs."bucketMonthly";