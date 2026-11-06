{{ config(materialized='table') }}

WITH spine AS (
    {{ dbt_utils.date_spine(
        datepart="day",
        start_date="CAST('2016-01-01' AS DATE)",
        end_date="CAST('2020-12-31' AS DATE)"
    ) }}
)

, renamed AS (
    SELECT
        CAST(date_day AS DATE) AS date_day
    FROM spine
)

SELECT * FROM renamed
