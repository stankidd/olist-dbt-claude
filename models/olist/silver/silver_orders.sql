WITH orders AS (
    SELECT * FROM {{ ref('bronze_orders') }}
)

, customers AS (
    SELECT * FROM {{ ref('bronze_customers') }}
)

, payments AS (
    SELECT * FROM {{ ref('int_order_payments') }}
)

, joined AS (
    SELECT
        o.order_id
        , o.customer_id
        , c.customer_unique_id
        , c.customer_zip_code_prefix
        , c.customer_city
        , c.customer_state
        , o.order_status
        , o.order_purchase_timestamp
        , o.order_approved_at
        , o.order_delivered_carrier_date
        , o.order_delivered_customer_date
        , o.order_estimated_delivery_date
        , p.payment_type
        , p.payment_installments
        , p.total_payment_value
        , p.payment_count
    FROM orders AS o
    LEFT JOIN customers AS c
        ON o.customer_id = c.customer_id
    LEFT JOIN payments AS p
        ON o.order_id = p.order_id
)

, enriched AS (
    SELECT
        order_id
        , customer_id
        , customer_unique_id
        , customer_zip_code_prefix
        , customer_city
        , customer_state
        , order_status
        , order_purchase_timestamp
        , order_approved_at
        , order_delivered_carrier_date
        , order_delivered_customer_date
        , order_estimated_delivery_date
        , payment_type
        , payment_installments
        , total_payment_value
        , payment_count
        , order_status = 'delivered' AS is_delivered
        , CAST(order_purchase_timestamp AS DATE) AS order_purchase_date
        , DATE_TRUNC('month', order_purchase_timestamp) AS order_purchase_month
        , {{ dbt.datediff('order_purchase_timestamp', 'order_delivered_customer_date', 'day') }} AS delivery_days
        , {{ dbt.datediff('order_purchase_timestamp', 'order_estimated_delivery_date', 'day') }} AS estimated_delivery_days
        , {{ dbt.datediff('order_purchase_timestamp', 'order_delivered_customer_date', 'day') }}
            - {{ dbt.datediff('order_purchase_timestamp', 'order_estimated_delivery_date', 'day') }} AS delivery_delay_days
        , CASE
            WHEN order_delivered_customer_date IS NULL THEN NULL
            ELSE order_delivered_customer_date <= order_estimated_delivery_date
          END AS is_on_time
        , CASE
            WHEN order_delivered_customer_date IS NULL THEN NULL
            ELSE order_delivered_customer_date > order_estimated_delivery_date
          END AS is_late_delivery
    FROM joined
)

SELECT * FROM enriched
