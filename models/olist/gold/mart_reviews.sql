WITH reviews AS (
    SELECT * FROM {{ ref('silver_order_reviews') }}
)

, orders AS (
    SELECT
        order_id
        , customer_unique_id
        , customer_state
        , delivery_days
    FROM {{ ref('silver_orders') }}
)

, first_items AS (
    SELECT
        order_id
        , product_category
        , seller_id
        , seller_state
    FROM {{ ref('silver_order_items') }}
    WHERE is_first_item
)

, joined AS (
    SELECT
        r.review_order_key
        , r.review_id
        , r.order_id
        , r.customer_id
        , o.customer_unique_id
        , o.customer_state
        , r.review_score
        , r.sentiment_bucket
        , r.has_comment
        , CAST(r.review_creation_date AS DATE) AS review_creation_date
        , r.response_time_days
        , r.review_sequence
        , r.order_status
        , fi.product_category
        , fi.seller_id
        , fi.seller_state
        , o.delivery_days
        , r.delivery_delay_days
        , r.is_late_delivery
    FROM reviews AS r
    LEFT JOIN orders AS o
        ON r.order_id = o.order_id
    LEFT JOIN first_items AS fi
        ON r.order_id = fi.order_id
)

SELECT * FROM joined
