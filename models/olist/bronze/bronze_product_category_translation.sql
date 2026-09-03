WITH source AS (
    SELECT * FROM {{ source('olist_raw', 'product_category_name_translation') }}
)

, renamed AS (
    SELECT
        CAST(product_category_name AS VARCHAR) AS product_category_name
        , CAST(product_category_name_english AS VARCHAR) AS product_category_name_english
    FROM source
)

SELECT * FROM renamed
