WITH order_items AS (
    SELECT * FROM {{ ref('bronze_order_items') }}
)

, orders AS (
    SELECT * FROM {{ ref('bronze_orders') }}
)

, customers AS (
    SELECT * FROM {{ ref('bronze_customers') }}
)

, products AS (
    SELECT * FROM {{ ref('bronze_products') }}
)

, category_translation AS (
    SELECT * FROM {{ ref('bronze_product_category_translation') }}
)

, sellers AS (
    SELECT * FROM {{ ref('bronze_sellers') }}
)

, joined AS (
    SELECT
        oi.order_item_key
        , oi.order_id
        , oi.order_item_id
        , oi.product_id
        , oi.seller_id
        , s.seller_state
        , c.customer_id
        , c.customer_unique_id
        , c.customer_state
        , o.order_status
        , o.order_purchase_timestamp
        , o.order_delivered_customer_date
        , o.order_estimated_delivery_date
        , oi.shipping_limit_date
        , oi.price
        , oi.freight_value
        , p.product_category_name
        , t.product_category_name_english
        , oi.order_item_id = 1 AS is_first_item
        , o.order_status = 'delivered' AS is_delivered
    FROM order_items AS oi
    LEFT JOIN orders AS o
        ON oi.order_id = o.order_id
    LEFT JOIN customers AS c
        ON o.customer_id = c.customer_id
    LEFT JOIN products AS p
        ON oi.product_id = p.product_id
    LEFT JOIN category_translation AS t
        ON p.product_category_name = t.product_category_name
    LEFT JOIN sellers AS s
        ON oi.seller_id = s.seller_id
)

, enriched AS (
    SELECT
        order_item_key
        , order_id
        , order_item_id
        , product_id
        , seller_id
        , seller_state
        , customer_id
        , customer_unique_id
        , customer_state
        , order_status
        , order_purchase_timestamp
        , order_delivered_customer_date
        , order_estimated_delivery_date
        , shipping_limit_date
        , price
        , freight_value
        , product_category_name
        , is_first_item
        , is_delivered
        , price + freight_value AS gmv
        , COALESCE(product_category_name_english, product_category_name, 'unknown') AS product_category
    FROM joined
)

SELECT * FROM enriched
