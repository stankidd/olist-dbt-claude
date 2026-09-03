# Olist Brazilian E-Commerce — Business Requirements Document

**Project:** olist-dbt-claude  
**Version:** 1.0  
**Status:** Approved for Tech Spec  
**Prepared by:** Stan Kidd — Cloud Analytics Consulting  
**Date:** September 2026  
**Purpose:** Public portfolio artifact demonstrating agentic dbt build capability  

---

## Business Context

Olist is a Brazilian e-commerce marketplace connector that enables small and 
medium merchants to sell through major Brazilian marketplaces (Americanas, 
Submarino, Shoptime, etc.) via a single contract. Olist handles the seller 
onboarding, logistics coordination, and customer communication on behalf of 
merchants.

The dataset covers 100,000 orders placed between 2016 and 2018 across multiple 
Brazilian states. It includes the full order lifecycle from purchase through 
delivery and customer review, enriched with product, seller, and geolocation data.

---

## Business Problem

The raw Olist dataset consists of 9 normalized source tables with no analytical 
layer. Business questions that cannot be answered from raw data without 
significant transformation:

- What is the overall order funnel conversion and where do orders drop off?
- Which product categories drive the most revenue and have the best delivery performance?
- Which sellers are top performers vs at-risk based on review scores and delivery times?
- What is the repeat purchase rate and how does customer LTV vary by cohort?
- How does review sentiment correlate with delivery performance and product category?

---

## Goals

1. Build a clean medallion warehouse (Bronze → Silver → Gold) on the Olist dataset
2. Deliver four business-domain gold models covering orders, customers, sellers, and reviews
3. Demonstrate end-to-end agentic dbt build using Claude Code + dbt MCP server
4. Produce a public, reproducible artifact that any engineer can clone and run

---

## Source Data

| Table | Rows | Description |
|-------|------|-------------|
| orders | 99,441 | Order header — status, timestamps, customer |
| order_items | 112,650 | Line items — product, seller, price, freight |
| order_payments | 103,886 | Payment methods and installments per order |
| order_reviews | 99,224 | Customer review scores and comments |
| customers | 99,441 | Customer zip code and state |
| sellers | 3,095 | Seller zip code and state |
| products | 32,951 | Product category, dimensions, weight |
| geolocation | 1,000,163 | Zip code to lat/lng mapping |
| product_category_name_translation | 71 | Portuguese to English category names |

---

## Grain Definitions

| Model | Grain |
|-------|-------|
| bronze_orders | One row per order |
| bronze_order_items | One row per order line item |
| bronze_order_payments | One row per payment record |
| bronze_order_reviews | One row per review |
| bronze_customers | One row per customer |
| bronze_sellers | One row per seller |
| bronze_products | One row per product |
| bronze_geolocation | One row per zip code observation |
| bronze_product_category_translation | One row per category |
| silver_orders | One row per order (enriched) |
| silver_order_items | One row per line item (enriched) |
| silver_customers | One row per customer (enriched) |
| silver_sellers | One row per seller (enriched) |
| mart_orders | One row per order (business metrics) |
| mart_customers | One row per customer (lifetime metrics) |
| mart_sellers | One row per seller (performance metrics) |
| mart_reviews | One row per review (sentiment + context) |

---

## Metrics Defined

### Order Metrics
| Metric | Definition |
|--------|-----------|
| gmv | SUM of order item price + freight value |
| avg_order_value | gmv / COUNT(distinct orders) |
| avg_items_per_order | COUNT(order_items) / COUNT(distinct orders) |
| delivery_days | DATEDIFF(day, order_purchase_timestamp, order_delivered_customer_date) |
| estimated_delivery_days | DATEDIFF(day, order_purchase_timestamp, order_estimated_delivery_date) |
| delivery_delay_days | delivery_days - estimated_delivery_days (positive = late) |
| on_time_delivery | delivery_delay_days <= 0 |
| order_status | delivered, shipped, canceled, unavailable, etc. |

### Customer Metrics
| Metric | Definition |
|--------|-----------|
| total_orders | COUNT(distinct order_id) per customer |
| total_spend | SUM(gmv) per customer |
| is_repeat_customer | total_orders > 1 |
| first_order_date | MIN(order_purchase_timestamp) |
| last_order_date | MAX(order_purchase_timestamp) |
| customer_lifespan_days | DATEDIFF(day, first_order_date, last_order_date) |
| avg_days_between_orders | customer_lifespan_days / (total_orders - 1) |
| customer_state | from customers table |

### Seller Metrics
| Metric | Definition |
|--------|-----------|
| total_orders | COUNT(distinct order_id) per seller |
| total_items_sold | COUNT(order_items) per seller |
| total_gmv | SUM(price + freight_value) per seller |
| avg_review_score | AVG(review_score) per seller |
| pct_5_star | COUNT(review_score=5) / total_orders |
| pct_1_star | COUNT(review_score=1) / total_orders |
| avg_delivery_days | AVG(delivery_days) per seller |
| on_time_delivery_rate | AVG(on_time_delivery) per seller |
| seller_state | from sellers table |

### Review Metrics
| Metric | Definition |
|--------|-----------|
| review_score | 1-5 star rating |
| has_comment | review_comment_message IS NOT NULL |
| sentiment_bucket | 1-2=Negative, 3=Neutral, 4-5=Positive |
| response_time_days | DATEDIFF(day, review_creation_date, review_answer_timestamp) |
| product_category | from products + translation |
| delivery_delay_days | from silver_orders join |

---

## Business Rules

| Rule | Definition |
|------|-----------|
| Valid order | order_status = 'delivered' for revenue metrics |
| GMV calculation | price + freight_value per line item |
| Repeat customer | customer has more than 1 order |
| On-time delivery | order_delivered_customer_date <= order_estimated_delivery_date |
| Late delivery | order_delivered_customer_date > order_estimated_delivery_date |
| Positive review | review_score >= 4 |
| Negative review | review_score <= 2 |
| Neutral review | review_score = 3 |
| Category translation | JOIN products to product_category_name_translation on product_category_name |
| Geolocation join | JOIN on customer_zip_code_prefix to geolocation (first match only — zip codes have multiple lat/lng observations) |

---

## Gold Models — Four Business Domains

### mart_orders
One row per order. Covers the full order lifecycle with delivery performance 
and payment summary.

Key columns:
- order_id, customer_id, order_status
- order_purchase_timestamp, order_delivered_customer_date
- delivery_days, delivery_delay_days, is_on_time
- total_items, total_gmv, avg_item_price
- payment_type (most common for order), payment_installments
- customer_state, seller_state (from first item)

### mart_customers
One row per customer. Lifetime value and purchase behavior metrics.

Key columns:
- customer_id, customer_unique_id, customer_state
- first_order_date, last_order_date
- total_orders, total_items, total_spend
- avg_order_value, is_repeat_customer
- avg_review_score (reviews left by this customer)
- customer_lifespan_days, avg_days_between_orders

### mart_sellers
One row per seller. Performance scorecard.

Key columns:
- seller_id, seller_state
- total_orders, total_items_sold, total_gmv
- avg_review_score, pct_5_star, pct_1_star
- avg_delivery_days, on_time_delivery_rate
- unique_customers, unique_product_categories
- seller_tier (derived: Gold/Silver/Bronze based on gmv + review score)

### mart_reviews
One row per review. Sentiment analysis with order and delivery context.

Key columns:
- review_id, order_id, customer_id
- review_score, sentiment_bucket, has_comment
- review_creation_date, response_time_days
- product_category (from order items)
- delivery_delay_days (from order)
- is_late_delivery (boolean)

---

## Architecture

```
olist-data/olist.duckdb (raw schema)
  customers, geolocation, orders, order_items,
  order_payments, order_reviews, products,
  sellers, product_category_name_translation
          |
          v
  Bronze Layer (9 models — views)
  Parse, rename, cast. No business logic.
          |
          v
  Silver Layer (4 models — tables)
  Join, enrich, apply business rules.
  silver_orders, silver_order_items,
  silver_customers, silver_sellers
          |
          v
  Gold Layer / Marts (4 models — tables)
  Business metrics by domain.
  mart_orders, mart_customers,
  mart_sellers, mart_reviews
```

---

## DuckDB-Specific Notes

- Source tables live in the `raw` schema of the DuckDB file
- dbt dev schema: `main` (DuckDB default)
- Bronze models materialized as views (zero storage cost)
- Silver and Gold models materialized as tables
- Geolocation table (1M rows) — deduplicate to one row per zip code prefix
  using ROW_NUMBER() before joining to avoid fan-out
- No MFA required — DuckDB is local file-based

---

## Reproducibility Requirements

Any engineer should be able to:
1. Clone the repo
2. Download the Olist dataset from Kaggle
3. Run the Python loader script to populate DuckDB
4. Run `dbt build` to build all models
5. Query the gold models

Total setup time target: under 15 minutes

---

## Out of Scope

- Real-time or streaming data
- Geospatial analysis (lat/lng available but not used in gold layer)
- Price inflation adjustment (BRL values used as-is)
- Seller fraud detection
- Marketing attribution

---

## Success Criteria

- All 17 models build without errors
- All dbt tests pass
- mart_orders row count matches delivered orders in source
- mart_customers row count matches unique customers in source
- mart_sellers row count matches sellers with at least one order
- mart_reviews row count matches reviews with valid order joins
- Full build completes in under 60 seconds on DuckDB
- Any engineer can clone and run with zero cloud accounts
