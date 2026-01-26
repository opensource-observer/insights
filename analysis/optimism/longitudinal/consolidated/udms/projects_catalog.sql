-- optimism.grants.projects_catalog

WITH base AS (
  SELECT
    gc.application_name,
    nullif(gc.oso_project_slug,'') AS oso_project_slug,
    lower(regexp_extract(gc.application_url,'(0x[0-9a-fA-F]+)',1)) AS atlas_project_id
  FROM optimism.grants.grants_consolidated gc
),
enriched AS (
  SELECT
    b.application_name,
    b.oso_project_slug,
    b.atlas_project_id,

    ossd.project_id AS ossd_project_id,
    ossd.display_name AS ossd_project_name,

    atlas.project_id AS atlas_project_id_mapped,
    atlas.display_name AS atlas_project_name
  FROM base b
  LEFT JOIN oso.projects_v1 ossd
    ON b.oso_project_slug=ossd.project_name
    AND ossd.project_source='OSS_DIRECTORY'
  LEFT JOIN oso.projects_v1 atlas
    ON b.atlas_project_id=atlas.project_name
    AND atlas.project_source='OP_ATLAS'
),
classified AS (
  SELECT
    *,
    CASE
      WHEN oso_project_slug IS NOT NULL AND ossd_project_id IS NOT NULL THEN 1
      WHEN oso_project_slug IS NULL AND atlas_project_id IS NOT NULL AND atlas_project_id_mapped IS NOT NULL THEN 2
      ELSE 3
    END AS priority_class,
    CASE
      WHEN oso_project_slug IS NOT NULL AND ossd_project_id IS NOT NULL THEN cast(ossd_project_id AS VARCHAR)
      WHEN oso_project_slug IS NULL AND atlas_project_id IS NOT NULL AND atlas_project_id_mapped IS NOT NULL THEN cast(atlas_project_id_mapped AS VARCHAR)
      ELSE concat('unmapped:',coalesce(atlas_project_id,lower(trim(application_name)),'unknown'))
    END AS entity_key
  FROM enriched
),
rolled AS (
  SELECT
    entity_key,
    min(priority_class) AS priority_class,
    max_by(ossd_project_id,CASE WHEN priority_class=1 THEN 1 ELSE 0 END) AS ossd_project_id_pick,
    max_by(ossd_project_name,CASE WHEN priority_class=1 THEN 1 ELSE 0 END) AS ossd_project_name_pick,
    max_by(oso_project_slug,CASE WHEN priority_class=1 THEN 1 ELSE 0 END) AS oso_project_slug_pick,
    max_by(atlas_project_id_mapped,CASE WHEN priority_class=2 THEN 1 ELSE 0 END) AS atlas_project_id_pick,
    max_by(atlas_project_name,CASE WHEN priority_class=2 THEN 1 ELSE 0 END) AS atlas_project_name_pick,

    array_sort(array_distinct(array_agg(atlas_project_id) FILTER (WHERE atlas_project_id IS NOT NULL))) AS atlas_project_ids,
    array_sort(array_distinct(array_agg(application_name) FILTER (WHERE application_name IS NOT NULL))) AS application_names
  FROM classified
  GROUP BY 1
)
SELECT
  CASE
    WHEN priority_class=1 THEN ossd_project_id_pick
    WHEN priority_class=2 THEN atlas_project_id_pick
    ELSE NULL
  END AS oso_project_id,
  CASE
    WHEN priority_class=1 THEN coalesce(ossd_project_name_pick,oso_project_slug_pick)
    WHEN priority_class=2 THEN atlas_project_name_pick
    ELSE element_at(application_names,1)
  END AS project_name,
  CASE
    WHEN priority_class=1 THEN oso_project_slug_pick
    ELSE NULL
  END AS oso_project_slug,
  CASE
    WHEN priority_class IN (1,2) THEN atlas_project_ids
    ELSE array[]
  END AS atlas_project_ids,
  application_names
FROM rolled