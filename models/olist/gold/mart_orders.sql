WITH orders AS (
    SELECT * FROM {{ ref('silver_orders') }}
    WHERE is_delivered
)

, item_agg AS (
    SELECT
        order_id
        , COUNT(*) AS total_items
        , SUM(gmv) AS total_gmv
        , AVG(price) AS avg_item_price
        , COUNT(DISTINCT seller_id) AS distinct_sellers
    FROM {{ ref('silver_order_items') }}
    GROUP BY 1
)

, first_item AS (
    SELECT
        order_id
        , seller_id
        , seller_state
        , product_category AS primary_product_category
    FROM {{ ref('silver_order_items') }}
    WHERE is_first_item
)

, joined AS (
    SELECT
        o.order_id
        , o.customer_id
        , o.customer_unique_id
        , o.order_status
        , o.order_purchase_timestamp
        , o.order_purchase_date
        , o.order_delivered_customer_date
        , o.order_estimated_delivery_date
        , o.delivery_days
        , o.estimated_delivery_days
        , o.delivery_delay_days
        , o.is_on_time
        , i.total_items
        , CAST(i.total_gmv AS DECIMAL(12, 2)) AS total_gmv
        , CAST(i.avg_item_price AS DECIMAL(12, 2)) AS avg_item_price
        , i.distinct_sellers
        , o.payment_type
        , o.payment_installments
        , CAST(o.total_payment_value AS DECIMAL(12, 2)) AS total_payment_value
        , o.customer_state
        , f.seller_id
        , f.seller_state
        , f.primary_product_category
    FROM orders AS o
    LEFT JOIN item_agg AS i
        ON o.order_id = i.order_id
    LEFT JOIN first_item AS f
        ON o.order_id = f.order_id
)

SELECT * FROM joined
