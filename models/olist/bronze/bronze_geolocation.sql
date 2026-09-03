WITH source AS (
    SELECT * FROM {{ source('olist_raw', 'geolocation') }}
)

, renamed AS (
    SELECT
        CAST(geolocation_zip_code_prefix AS VARCHAR) AS zip_code_prefix
        , CAST(geolocation_lat AS DOUBLE) AS latitude
        , CAST(geolocation_lng AS DOUBLE) AS longitude
        , CAST(geolocation_city AS VARCHAR) AS city
        , CAST(geolocation_state AS VARCHAR) AS state
    FROM source
)

SELECT * FROM renamed
