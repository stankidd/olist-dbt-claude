WITH sellers AS (
    SELECT * FROM {{ ref('bronze_sellers') }}
)

, geolocation AS (
    SELECT * FROM {{ ref('int_geolocation_deduped') }}
)

, joined AS (
    SELECT
        s.seller_id
        , s.seller_zip_code_prefix
        , s.seller_city
        , s.seller_state
        , g.latitude
        , g.longitude
        , g.zip_code_prefix IS NOT NULL AS has_geolocation
    FROM sellers AS s
    LEFT JOIN geolocation AS g
        ON s.seller_zip_code_prefix = g.zip_code_prefix
)

SELECT * FROM joined
