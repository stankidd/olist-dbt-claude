WITH source AS (
    SELECT * FROM {{ source('olist_raw', 'order_reviews') }}
)

, renamed AS (
    SELECT
        {{ dbt_utils.generate_surrogate_key(['review_id', 'order_id']) }} AS review_order_key
        , CAST(review_id AS VARCHAR) AS review_id
        , CAST(order_id AS VARCHAR) AS order_id
        , CAST(review_score AS INTEGER) AS review_score
        , CAST(review_comment_title AS VARCHAR) AS review_comment_title
        , CAST(review_comment_message AS VARCHAR) AS review_comment_message
        , CAST(review_creation_date AS TIMESTAMP) AS review_creation_date
        , CAST(review_answer_timestamp AS TIMESTAMP) AS review_answer_timestamp
    FROM source
)

SELECT * FROM renamed
