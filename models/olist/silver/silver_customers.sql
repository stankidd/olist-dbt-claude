WITH customers AS (
    SELECT * FROM {{ ref('bronze_customers') }}
)

, geolocation AS (
    SELECT * FROM {{ ref('int_geolocation_deduped') }}
)

, joined AS (
    SELECT
        c.customer_id
        , c.customer_unique_id
        , c.customer_zip_code_prefix
        , c.customer_city
        , c.customer_state
        , g.latitude
        , g.longitude
        , g.zip_code_prefix IS NOT NULL AS has_geolocation
    FROM customers AS c
    LEFT JOIN geolocation AS g
        ON c.customer_zip_code_prefix = g.zip_code_prefix
)

SELECT * FROM joined
