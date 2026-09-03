WITH source AS (
    SELECT * FROM {{ source('olist_raw', 'sellers') }}
)

, renamed AS (
    SELECT
        CAST(seller_id AS VARCHAR) AS seller_id
        , CAST(seller_zip_code_prefix AS VARCHAR) AS seller_zip_code_prefix
        , CAST(seller_city AS VARCHAR) AS seller_city
        , CAST(seller_state AS VARCHAR) AS seller_state
    FROM source
)

SELECT * FROM renamed
