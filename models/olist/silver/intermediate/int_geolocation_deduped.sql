WITH geolocation AS (
    SELECT * FROM {{ ref('bronze_geolocation') }}
)

, ranked AS (
    SELECT
        zip_code_prefix
        , latitude
        , longitude
        , city
        , state
        , ROW_NUMBER() OVER (PARTITION BY zip_code_prefix ORDER BY latitude, longitude, city) AS row_num
        , COUNT(*) OVER (PARTITION BY zip_code_prefix) AS observation_count
    FROM geolocation
)

, deduped AS (
    SELECT
        zip_code_prefix
        , latitude
        , longitude
        , city
        , state
        , observation_count
    FROM ranked
    WHERE row_num = 1
)

SELECT * FROM deduped
