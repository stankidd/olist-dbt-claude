WITH source AS (
    SELECT * FROM {{ source('olist_raw', 'customers') }}
)

, renamed AS (
    SELECT
        CAST(customer_id AS VARCHAR) AS customer_id
        , CAST(customer_unique_id AS VARCHAR) AS customer_unique_id
        , CAST(customer_zip_code_prefix AS VARCHAR) AS customer_zip_code_prefix
        , CAST(customer_city AS VARCHAR) AS customer_city
        , CAST(customer_state AS VARCHAR) AS customer_state
    FROM source
)

SELECT * FROM renamed
