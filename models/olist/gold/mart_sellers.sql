WITH activity AS (
    SELECT
        seller_id
        , COUNT(DISTINCT order_id) AS total_orders
        , COUNT(*) AS total_items_sold
        , COUNT(DISTINCT customer_unique_id) AS unique_customers
        , COUNT(DISTINCT product_category) AS unique_product_categories
    FROM {{ ref('silver_order_items') }}
    GROUP BY 1
)

, revenue AS (
    SELECT
        seller_id
        , SUM(gmv) AS total_gmv
        , COUNT(DISTINCT order_id) AS delivered_orders
    FROM {{ ref('silver_order_items') }}
    WHERE is_delivered
    GROUP BY 1
)

, delivered_seller_orders AS (
    SELECT DISTINCT
        oi.seller_id
        , oi.order_id
        , o.delivery_days
        , o.is_on_time
    FROM {{ ref('silver_order_items') }} AS oi
    INNER JOIN {{ ref('silver_orders') }} AS o
        ON oi.order_id = o.order_id
    WHERE o.is_delivered
)

, delivery AS (
    SELECT
        seller_id
        , AVG(delivery_days) AS avg_delivery_days
        , AVG(
            CASE
                WHEN is_on_time IS NULL THEN NULL
                WHEN is_on_time THEN 1.0
                ELSE 0.0
            END
          ) AS on_time_delivery_rate
    FROM delivered_seller_orders
    GROUP BY 1
)

, seller_reviews AS (
    SELECT DISTINCT
        oi.seller_id
        , r.review_order_key
        , r.review_score
    FROM {{ ref('silver_order_items') }} AS oi
    INNER JOIN {{ ref('silver_order_reviews') }} AS r
        ON oi.order_id = r.order_id
)

, reviews AS (
    SELECT
        seller_id
        , AVG(review_score) AS avg_review_score
        , COUNT(*) AS total_reviews
        , SUM(CASE WHEN review_score = 5 THEN 1 ELSE 0 END) AS five_star_reviews
        , SUM(CASE WHEN review_score = 1 THEN 1 ELSE 0 END) AS one_star_reviews
    FROM seller_reviews
    GROUP BY 1
)

, joined AS (
    SELECT
        s.seller_id
        , s.seller_state
        , s.seller_city
        , a.total_orders
        , COALESCE(rv.delivered_orders, 0) AS delivered_orders
        , a.total_items_sold
        , CAST(COALESCE(rv.total_gmv, 0) AS DECIMAL(12, 2)) AS total_gmv
        , a.unique_customers
        , a.unique_product_categories
        , CAST(rw.avg_review_score AS DECIMAL(4, 2)) AS avg_review_score
        , COALESCE(rw.total_reviews, 0) AS total_reviews
        , CAST(rw.five_star_reviews AS DECIMAL(12, 4)) / NULLIF(rw.total_reviews, 0) AS pct_5_star
        , CAST(rw.one_star_reviews AS DECIMAL(12, 4)) / NULLIF(rw.total_reviews, 0) AS pct_1_star
        , CAST(d.avg_delivery_days AS DECIMAL(6, 2)) AS avg_delivery_days
        , CAST(d.on_time_delivery_rate AS DECIMAL(5, 4)) AS on_time_delivery_rate
        , CASE
            WHEN COALESCE(rv.total_gmv, 0) >= 10000 AND rw.avg_review_score >= 4.0 THEN 'Gold'
            WHEN COALESCE(rv.total_gmv, 0) >= 1000 AND rw.avg_review_score >= 3.5 THEN 'Silver'
            ELSE 'Bronze'
          END AS seller_tier
    FROM {{ ref('silver_sellers') }} AS s
    LEFT JOIN activity AS a
        ON s.seller_id = a.seller_id
    LEFT JOIN revenue AS rv
        ON s.seller_id = rv.seller_id
    LEFT JOIN delivery AS d
        ON s.seller_id = d.seller_id
    LEFT JOIN reviews AS rw
        ON s.seller_id = rw.seller_id
)

SELECT * FROM joined
