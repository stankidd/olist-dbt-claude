WITH source AS (
    SELECT * FROM {{ source('olist_raw', 'order_payments') }}
)

, renamed AS (
    SELECT
        {{ dbt_utils.generate_surrogate_key(['order_id', 'payment_sequential']) }} AS order_payment_key
        , CAST(order_id AS VARCHAR) AS order_id
        , CAST(payment_sequential AS INTEGER) AS payment_sequential
        , CAST(payment_type AS VARCHAR) AS payment_type
        , CAST(payment_installments AS INTEGER) AS payment_installments
        , CAST(payment_value AS DECIMAL(10, 2)) AS payment_value
    FROM source
)

SELECT * FROM renamed
