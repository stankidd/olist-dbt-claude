WITH source AS (
    SELECT * FROM {{ source('olist_raw', 'products') }}
)

, renamed AS (
    SELECT
        CAST(product_id AS VARCHAR) AS product_id
        , CAST(product_category_name AS VARCHAR) AS product_category_name
        , CAST(product_name_lenght AS INTEGER) AS product_name_length
        , CAST(product_description_lenght AS INTEGER) AS product_description_length
        , CAST(product_photos_qty AS INTEGER) AS product_photos_qty
        , CAST(product_weight_g AS INTEGER) AS product_weight_g
        , CAST(product_length_cm AS INTEGER) AS product_length_cm
        , CAST(product_height_cm AS INTEGER) AS product_height_cm
        , CAST(product_width_cm AS INTEGER) AS product_width_cm
    FROM source
)

SELECT * FROM renamed
