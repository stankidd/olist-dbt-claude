WITH reviews AS (
    SELECT * FROM {{ ref('bronze_order_reviews') }}
)

, orders AS (
    SELECT * FROM {{ ref('bronze_orders') }}
)

, joined AS (
    SELECT
        r.review_order_key
        , r.review_id
        , r.order_id
        , o.customer_id
        , o.order_status
        , r.review_score
        , r.review_comment_title
        , r.review_comment_message
        , r.review_creation_date
        , r.review_answer_timestamp
        , o.order_purchase_timestamp
        , o.order_delivered_customer_date
        , o.order_estimated_delivery_date
    FROM reviews AS r
    LEFT JOIN orders AS o
        ON r.order_id = o.order_id
)

, enriched AS (
    SELECT
        review_order_key
        , review_id
        , order_id
        , customer_id
        , order_status
        , review_score
        , review_comment_title
        , review_comment_message
        , review_creation_date
        , review_answer_timestamp
        , CASE
            WHEN review_score <= 2 THEN 'Negative'
            WHEN review_score = 3 THEN 'Neutral'
            ELSE 'Positive'
          END AS sentiment_bucket
        , NULLIF(TRIM(review_comment_message), '') IS NOT NULL AS has_comment
        , NULLIF(TRIM(review_comment_title), '') IS NOT NULL AS has_title
        , {{ dbt.datediff('review_creation_date', 'review_answer_timestamp', 'day') }} AS response_time_days
        , {{ dbt.datediff('order_purchase_timestamp', 'order_delivered_customer_date', 'day') }}
            - {{ dbt.datediff('order_purchase_timestamp', 'order_estimated_delivery_date', 'day') }} AS delivery_delay_days
        , CASE
            WHEN order_delivered_customer_date IS NULL THEN NULL
            ELSE order_delivered_customer_date > order_estimated_delivery_date
          END AS is_late_delivery
        , ROW_NUMBER() OVER (
            PARTITION BY order_id
            ORDER BY review_creation_date, review_answer_timestamp, review_id
          ) AS review_sequence
    FROM joined
)

SELECT * FROM enriched
