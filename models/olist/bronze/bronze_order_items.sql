WITH source AS (
    SELECT * FROM {{ source('olist_raw', 'order_items') }}
)

, renamed AS (
    SELECT
        {{ dbt_utils.generate_surrogate_key(['order_id', 'order_item_id']) }} AS order_item_key
        , CAST(order_id AS VARCHAR) AS order_id
        , CAST(order_item_id AS INTEGER) AS order_item_id
        , CAST(product_id AS VARCHAR) AS product_id
        , CAST(seller_id AS VARCHAR) AS seller_id
        , CAST(shipping_limit_date AS TIMESTAMP) AS shipping_limit_date
        , CAST(price AS DECIMAL(10, 2)) AS price
        , CAST(freight_value AS DECIMAL(10, 2)) AS freight_value
    FROM source
)

SELECT * FROM renamed
