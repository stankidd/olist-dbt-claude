WITH order_payments AS (
    SELECT * FROM {{ ref('bronze_order_payments') }}
)

, by_type AS (
    SELECT
        order_id
        , payment_type
        , COUNT(*) AS type_count
        , SUM(payment_value) AS type_value
    FROM order_payments
    GROUP BY 1, 2
)

, ranked AS (
    SELECT
        order_id
        , payment_type
        , ROW_NUMBER() OVER (
            PARTITION BY order_id
            ORDER BY type_count DESC, type_value DESC, payment_type
        ) AS type_rank
    FROM by_type
)

, totals AS (
    SELECT
        order_id
        , SUM(payment_value) AS total_payment_value
        , MAX(payment_installments) AS payment_installments
        , COUNT(*) AS payment_count
        , COUNT(DISTINCT payment_type) AS payment_type_count
    FROM order_payments
    GROUP BY 1
)

, joined AS (
    SELECT
        t.order_id
        , r.payment_type
        , t.payment_installments
        , t.total_payment_value
        , t.payment_count
        , t.payment_type_count
    FROM totals AS t
    LEFT JOIN ranked AS r
        ON t.order_id = r.order_id
        AND r.type_rank = 1
)

SELECT * FROM joined
