WITH customer_orders AS (
    SELECT
        c.customer_unique_id
        , o.customer_state
        , o.customer_city
        , ROW_NUMBER() OVER (
            PARTITION BY c.customer_unique_id
            ORDER BY o.order_purchase_timestamp DESC
        ) AS recency_rank
    FROM {{ ref('silver_customers') }} AS c
    INNER JOIN {{ ref('silver_orders') }} AS o
        ON c.customer_id = o.customer_id
)

, customer_base AS (
    SELECT
        customer_unique_id
        , customer_state
        , customer_city
    FROM customer_orders
    WHERE recency_rank = 1
)

, order_agg AS (
    SELECT
        customer_unique_id
        , COUNT(DISTINCT order_id) AS total_orders
        , COUNT(DISTINCT CASE WHEN is_delivered THEN order_id END) AS delivered_orders
        , CAST(MIN(order_purchase_timestamp) AS DATE) AS first_order_date
        , CAST(MAX(order_purchase_timestamp) AS DATE) AS last_order_date
    FROM {{ ref('silver_orders') }}
    GROUP BY 1
)

, spend_agg AS (
    SELECT
        customer_unique_id
        , COUNT(*) AS total_items
        , SUM(gmv) AS total_spend
    FROM {{ ref('silver_order_items') }}
    WHERE is_delivered
    GROUP BY 1
)

, review_agg AS (
    SELECT
        o.customer_unique_id
        , AVG(r.review_score) AS avg_review_score
        , COUNT(*) AS total_reviews
    FROM {{ ref('silver_order_reviews') }} AS r
    INNER JOIN {{ ref('silver_orders') }} AS o
        ON r.order_id = o.order_id
    GROUP BY 1
)

, joined AS (
    SELECT
        b.customer_unique_id
        , b.customer_state
        , b.customer_city
        , oa.first_order_date
        , oa.last_order_date
        , oa.total_orders
        , oa.delivered_orders
        , COALESCE(sa.total_items, 0) AS total_items
        , CAST(COALESCE(sa.total_spend, 0) AS DECIMAL(12, 2)) AS total_spend
        , CAST(COALESCE(sa.total_spend, 0) / NULLIF(oa.delivered_orders, 0) AS DECIMAL(12, 2)) AS avg_order_value
        , oa.total_orders > 1 AS is_repeat_customer
        , CAST(ra.avg_review_score AS DECIMAL(4, 2)) AS avg_review_score
        , COALESCE(ra.total_reviews, 0) AS total_reviews
        , {{ dbt.datediff('oa.first_order_date', 'oa.last_order_date', 'day') }} AS customer_lifespan_days
        , CAST(
            {{ dbt.datediff('oa.first_order_date', 'oa.last_order_date', 'day') }}
            AS DECIMAL(10, 2)
          ) / NULLIF(oa.total_orders - 1, 0) AS avg_days_between_orders
    FROM customer_base AS b
    LEFT JOIN order_agg AS oa
        ON b.customer_unique_id = oa.customer_unique_id
    LEFT JOIN spend_agg AS sa
        ON b.customer_unique_id = sa.customer_unique_id
    LEFT JOIN review_agg AS ra
        ON b.customer_unique_id = ra.customer_unique_id
)

SELECT * FROM joined
