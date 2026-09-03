# Olist Brazilian E-Commerce -- Technical Specification

**Client:** Olist (public Kaggle dataset, portfolio project)
**BRD Source:** `.claude/project_docs/client-olist/03-requirements/olist-brd.md`
**Author:** Stan Kidd
**Date:** 2026-09-01
**Status:** Validated 2026-09-01 -- Ready to Build
**Target:** DuckDB (`olist` profile, `C:/Users/Stan/Documents/VScode/olist-data/olist.duckdb`)

---

## Business Context

Olist connects small Brazilian merchants to major marketplaces under one contract
and handles logistics and customer communication on their behalf. The raw dataset
is 9 normalized tables covering ~100k orders from 2016 to 2018 with no analytical
layer. This pipeline builds a medallion warehouse that answers four questions:
how orders flow and deliver, what customers are worth over their lifetime, which
sellers perform or lag, and how review sentiment relates to delivery experience.

---

## Deviations From the BRD (read first)

Profiling the raw data on 2026-09-01 surfaced facts the BRD did not anticipate.
Each item below changes the design and needs stakeholder awareness before build.

| # | BRD assumption | What the data shows | Decision in this spec |
|---|----------------|---------------------|-----------------------|
| 1 | mart_reviews grain is "one row per review" keyed by review_id | review_id is **not unique**: 99,224 rows, 98,410 distinct review_ids, 789 review_ids attached to 2+ orders. (review_id, order_id) is unique. | Grain is one row per review-order pair. Surrogate key `review_order_key` = surrogate of (review_id, order_id). |
| 2 | mart_customers grain is customer_id with total_orders and repeat flag | customer_id is issued **per order** (99,441 customers = 99,441 orders). The person is customer_unique_id (96,096 distinct, 2,997 repeaters). At customer_id grain every customer has exactly 1 order and repeat rate is 0. | gold_customers grain is customer_unique_id. customer_id is dropped from gold (it is per-order). Row count target 96,096 matches the BRD success criterion. |
| 3 | mart_orders is "one row per order" but success criterion says row count = delivered orders | 96,478 of 99,441 orders are delivered. Funnel analysis needs all statuses. | silver_orders keeps all 8 statuses for funnel work. gold_orders is filtered to delivered only to satisfy the success criterion and the "valid order" rule. |
| 4 | pct_5_star = 5-star reviews / total_orders | 547 orders have 2 or 3 reviews, so review-based rates over an order denominator can exceed 100%. | Denominator is total_reviews, not total_orders. |
| 5 | payment_type is "most common for order" | 2,246 orders have 2+ payment types, 866 have differing installment counts, up to 29 payment rows per order. | Intermediate model picks the modal payment type (ties broken by highest summed payment_value, then alphabetical). payment_installments = MAX per order. |
| 6 | Model names mart_orders, mart_customers, mart_sellers, mart_reviews | Every other client in this repo uses a gold_ prefix and the folder is models/olist/gold. | Models are gold_orders, gold_customers, gold_sellers, gold_reviews. Rename is trivial if the mart_ names are preferred. |
| 7 | 17 models total (9 + 4 + 4) | Gold cannot read bronze, and reviews and payments have no silver home in the BRD. | 20 models: 9 bronze, 2 intermediate, 5 silver (adds silver_order_reviews), 4 gold. |
| 8 | seller_tier is "Gold/Silver/Bronze based on gmv + review score" with no thresholds | Delivered GMV per seller: p50 1,039, p75 4,159, p90 11,537 BRL. Avg review p25 3.79, p50 4.20. | Gold = gmv >= 10,000 AND avg_review_score >= 4.0 (221 sellers). Silver = gmv >= 1,000 AND avg_review_score >= 3.5 (1,121 sellers). Bronze = everyone else. |
| 9 | has_comment = review_comment_message IS NOT NULL | 9 rows hold an empty string rather than NULL. | has_comment = NULLIF(TRIM(review_comment_message), '') IS NOT NULL. |
| 10 | Category translation via join | 610 products have NULL category. 2 categories (13 products) have no English translation: pc_gamer, portateis_cozinha_e_preparadores_de_alimentos. | product_category = COALESCE(english_name, portuguese_name, 'unknown'). |

---

## Source Data

All sources live in the `raw` schema of the DuckDB file. No Snowflake objects
are involved. The dbt target schema defaults to `main`, so with the repo's
generate_schema_name macro dev objects land in `main_olist_bronze`,
`main_olist_silver`, and `main_olist_gold`.

| Table | Rows | Grain (verified) | Primary key | Notes |
|-------|------|------------------|-------------|-------|
| raw.orders | 99,441 | One row per order | order_id (unique) | 8 statuses. 8 delivered orders have NULL delivered date. |
| raw.order_items | 112,650 | One row per line item | (order_id, order_item_id) unique | Max 21 items per order. 1,278 orders span 2+ sellers. 775 orders (none delivered) have no items. |
| raw.order_payments | 103,886 | One row per payment record | (order_id, payment_sequential) unique | Up to 29 payments per order. 1 order has no payment. |
| raw.order_reviews | 99,224 | One row per review-order pair | (review_id, order_id) unique; review_id alone is NOT | 768 orders have no review. 547 orders have 2 to 3 reviews. |
| raw.customers | 99,441 | One row per order-customer | customer_id unique | customer_unique_id identifies the person (96,096 distinct). |
| raw.sellers | 3,095 | One row per seller | seller_id unique | All 3,095 sellers have at least one order item. |
| raw.products | 32,951 | One row per product | product_id unique | Column names misspelled in source: product_name_lenght, product_description_lenght. |
| raw.geolocation | 1,000,163 | One row per zip observation | none; 19,015 distinct zip prefixes, up to 1,146 rows per zip | Must be deduplicated before any join. |
| raw.product_category_name_translation | 71 | One row per category | product_category_name unique | 73 categories exist in products; 2 lack translation. |

### Data Profile Findings (verified 2026-09-01)

| Field | Profiled values |
|-------|-----------------|
| orders.order_status | delivered 96,478; shipped 1,107; canceled 625; unavailable 609; invoiced 314; processing 301; created 5; approved 2 |
| orders.order_purchase_timestamp | 2016-09-04 to 2018-10-17 |
| orders delivered late vs on time | 7,826 late, 88,644 on time, 8 delivered with NULL delivered date |
| orders delivery_days (delivered) | 0 to 210 days; no delivered-before-purchase rows |
| order_payments.payment_type | credit_card 76,795; boleto 19,784; voucher 5,775; debit_card 1,529; not_defined 3 |
| order_payments.payment_installments | 0 to 24 (0 occurs only on credit_card) |
| order_payments.payment_value | 0.00 to 13,664.08; 9 rows are 0.00 (6 voucher, 3 not_defined) |
| order_reviews.review_score | 1: 11,424; 2: 3,151; 3: 8,179; 4: 19,142; 5: 57,328 |
| order_reviews.review_comment_message | 40,977 non-null, 9 of those blank |
| order_reviews.review_creation_date | 2016-10-02 to 2018-08-31; answer timestamp always present and never before creation |
| order_reviews response time | 0 to 518 days |
| order_items.price | 0.85 to 6,735.00; no nulls |
| order_items.freight_value | 0.00 minimum; no nulls |
| customers.customer_state | 27 Brazilian state codes (SP 41,746 largest, RR 46 smallest) |
| sellers.seller_state | 23 state codes (SP 1,849 largest) |
| zip_code_prefix | Always 5 characters, stored as VARCHAR (leading zeros preserved) |
| geolocation coverage | 278 customer zips and 7 seller zips have no geolocation match |
| repeat customers | 2,997 customer_unique_ids with 2+ customer_ids; 39 of those appear in more than one state |

### Referential integrity (all verified zero orphans)

order_items to orders, order_items to products, order_items to sellers,
orders to customers, order_payments to orders, order_reviews to orders.

---

## Architecture Overview

```
olist.duckdb  schema raw
  orders, order_items, order_payments, order_reviews, customers,
  sellers, products, geolocation, product_category_name_translation
        |
        v  source('olist_raw', ...)
  Bronze (9 views -- rename, cast, add technical keys; no filters, no joins)
  bronze_orders                  bronze_customers
  bronze_order_items             bronze_sellers
  bronze_order_payments          bronze_products
  bronze_order_reviews           bronze_geolocation
  bronze_product_category_translation
        |
        v
  Intermediate (2 tables, in models/olist/silver/intermediate/)
  int_geolocation_deduped        (one row per zip_code_prefix)
  int_order_payments             (one row per order: modal type, max installments, total paid)
        |
        v
  Silver (5 tables -- joins, business rules, derived columns)
  silver_orders                  (one row per order, all statuses)
  silver_order_items             (one row per line item, enriched)
  silver_customers               (one row per customer_id)
  silver_sellers                 (one row per seller)
  silver_order_reviews           (one row per review-order pair)
        |
        v
  Gold (4 tables -- business metrics by domain)
  gold_orders                    (one row per delivered order)
  gold_customers                 (one row per customer_unique_id)
  gold_sellers                   (one row per seller)
  gold_reviews                   (one row per review-order pair)
```

### Project configuration

dbt_project.yml already contains the `olist` block with bronze views and
silver/gold tables and custom schemas `olist_bronze`, `olist_silver`,
`olist_gold`. The intermediate folder sits under silver and inherits table
materialization and the `olist_silver` schema. No change needed.

`packages.yml` already includes dbt_utils, which this spec uses for
`generate_surrogate_key`, `expression_is_true`, and `accepted_range`.

### Source definition

File: `models/olist/bronze/olist_sources.yml`

```yaml
version: 2

sources:
  - name: olist_raw
    description: "Olist Brazilian e-commerce raw tables loaded from Kaggle CSVs into DuckDB"
    schema: raw
    tables:
      - name: orders
      - name: order_items
      - name: order_payments
      - name: order_reviews
      - name: customers
      - name: sellers
      - name: products
      - name: geolocation
      - name: product_category_name_translation
```

No `database:` key. dbt-duckdb resolves the source to the attached catalog.

### Portability rule

Use `{{ dbt.datediff('start_col', 'end_col', 'day') }}` for every day-difference
calculation instead of raw DATEDIFF so the models compile unchanged on Snowflake.
Use `{{ dbt_utils.generate_surrogate_key([...]) }}` for composite keys.

---

## Bronze Models

Rules for every bronze model: `SELECT` from one `source()`, rename to
snake_case, cast explicitly, no `WHERE`, no joins, no business logic,
materialize as view. Money columns cast to DECIMAL(10,2). Small integers cast
to INTEGER.

---

### bronze_orders

- **File:** `models/olist/bronze/bronze_orders.sql`
- **Source:** `source('olist_raw', 'orders')`
- **Grain:** One row per order (99,441 rows)
- **Purpose:** Typed order header with lifecycle timestamps

| Target Column | Source Column | Type | Notes |
|--------------|--------------|------|-------|
| order_id | order_id | VARCHAR | PK |
| customer_id | customer_id | VARCHAR | FK to bronze_customers |
| order_status | order_status | VARCHAR | 8 values, see profile |
| order_purchase_timestamp | order_purchase_timestamp | TIMESTAMP | never null |
| order_approved_at | order_approved_at | TIMESTAMP | null on 160 rows |
| order_delivered_carrier_date | order_delivered_carrier_date | TIMESTAMP | nullable |
| order_delivered_customer_date | order_delivered_customer_date | TIMESTAMP | null on 8 delivered orders |
| order_estimated_delivery_date | order_estimated_delivery_date | TIMESTAMP | never null |

Tests: order_id unique + not_null; customer_id not_null; order_status
accepted_values [delivered, shipped, canceled, unavailable, invoiced,
processing, created, approved]; order_purchase_timestamp not_null;
order_estimated_delivery_date not_null.

---

### bronze_order_items

- **File:** `models/olist/bronze/bronze_order_items.sql`
- **Source:** `source('olist_raw', 'order_items')`
- **Grain:** One row per order line item (112,650 rows)
- **Purpose:** Typed line items with technical composite key

| Target Column | Source Column | Type | Notes |
|--------------|--------------|------|-------|
| order_item_key | (derived) | VARCHAR | `generate_surrogate_key(['order_id', 'order_item_id'])` |
| order_id | order_id | VARCHAR | FK |
| order_item_id | order_item_id | INTEGER | 1-based sequence within order, max 21 |
| product_id | product_id | VARCHAR | FK |
| seller_id | seller_id | VARCHAR | FK |
| shipping_limit_date | shipping_limit_date | TIMESTAMP | |
| price | price | DECIMAL(10,2) | 0.85 to 6,735.00 |
| freight_value | freight_value | DECIMAL(10,2) | >= 0 |

Tests: order_item_key unique + not_null; order_id, product_id, seller_id
not_null; price and freight_value not_null.

---

### bronze_order_payments

- **File:** `models/olist/bronze/bronze_order_payments.sql`
- **Source:** `source('olist_raw', 'order_payments')`
- **Grain:** One row per payment record (103,886 rows)
- **Purpose:** Typed payment rows

| Target Column | Source Column | Type | Notes |
|--------------|--------------|------|-------|
| order_payment_key | (derived) | VARCHAR | `generate_surrogate_key(['order_id', 'payment_sequential'])` |
| order_id | order_id | VARCHAR | FK |
| payment_sequential | payment_sequential | INTEGER | 1 to 29 |
| payment_type | payment_type | VARCHAR | 5 values incl. not_defined |
| payment_installments | payment_installments | INTEGER | 0 to 24 |
| payment_value | payment_value | DECIMAL(10,2) | >= 0 |

Tests: order_payment_key unique + not_null; order_id not_null; payment_type
accepted_values [credit_card, boleto, voucher, debit_card, not_defined].

---

### bronze_order_reviews

- **File:** `models/olist/bronze/bronze_order_reviews.sql`
- **Source:** `source('olist_raw', 'order_reviews')`
- **Grain:** One row per review-order pair (99,224 rows)
- **Purpose:** Typed reviews with a technical key, because review_id alone is not unique

| Target Column | Source Column | Type | Notes |
|--------------|--------------|------|-------|
| review_order_key | (derived) | VARCHAR | `generate_surrogate_key(['review_id', 'order_id'])` |
| review_id | review_id | VARCHAR | NOT unique (98,410 distinct) |
| order_id | order_id | VARCHAR | FK |
| review_score | review_score | INTEGER | 1 to 5 |
| review_comment_title | review_comment_title | VARCHAR | nullable |
| review_comment_message | review_comment_message | VARCHAR | nullable, 9 blanks |
| review_creation_date | review_creation_date | TIMESTAMP | |
| review_answer_timestamp | review_answer_timestamp | TIMESTAMP | |

Tests: review_order_key unique + not_null; review_id, order_id not_null;
review_score accepted_values [1, 2, 3, 4, 5] (quote: false).

---

### bronze_customers

- **File:** `models/olist/bronze/bronze_customers.sql`
- **Source:** `source('olist_raw', 'customers')`
- **Grain:** One row per order-scoped customer record (99,441 rows)
- **Purpose:** Typed customer rows; keep the per-order id and the person id side by side

| Target Column | Source Column | Type | Notes |
|--------------|--------------|------|-------|
| customer_id | customer_id | VARCHAR | PK, one per order |
| customer_unique_id | customer_unique_id | VARCHAR | the person; 96,096 distinct |
| customer_zip_code_prefix | customer_zip_code_prefix | VARCHAR | 5 chars, keep as text |
| customer_city | customer_city | VARCHAR | |
| customer_state | customer_state | VARCHAR | 2-letter code |

Tests: customer_id unique + not_null; customer_unique_id not_null;
customer_state not_null.

---

### bronze_sellers

- **File:** `models/olist/bronze/bronze_sellers.sql`
- **Source:** `source('olist_raw', 'sellers')`
- **Grain:** One row per seller (3,095 rows)

| Target Column | Source Column | Type | Notes |
|--------------|--------------|------|-------|
| seller_id | seller_id | VARCHAR | PK |
| seller_zip_code_prefix | seller_zip_code_prefix | VARCHAR | 5 chars |
| seller_city | seller_city | VARCHAR | |
| seller_state | seller_state | VARCHAR | 2-letter code |

Tests: seller_id unique + not_null; seller_state not_null.

---

### bronze_products

- **File:** `models/olist/bronze/bronze_products.sql`
- **Source:** `source('olist_raw', 'products')`
- **Grain:** One row per product (32,951 rows)
- **Purpose:** Typed product catalog; corrects source misspellings

| Target Column | Source Column | Type | Notes |
|--------------|--------------|------|-------|
| product_id | product_id | VARCHAR | PK |
| product_category_name | product_category_name | VARCHAR | Portuguese; null on 610 rows |
| product_name_length | product_name_lenght | INTEGER | source typo corrected |
| product_description_length | product_description_lenght | INTEGER | source typo corrected |
| product_photos_qty | product_photos_qty | INTEGER | |
| product_weight_g | product_weight_g | INTEGER | |
| product_length_cm | product_length_cm | INTEGER | |
| product_height_cm | product_height_cm | INTEGER | |
| product_width_cm | product_width_cm | INTEGER | |

Tests: product_id unique + not_null.

---

### bronze_geolocation

- **File:** `models/olist/bronze/bronze_geolocation.sql`
- **Source:** `source('olist_raw', 'geolocation')`
- **Grain:** One row per zip observation (1,000,163 rows, not unique)
- **Purpose:** Typed pass-through; dedup happens in the intermediate layer

| Target Column | Source Column | Type | Notes |
|--------------|--------------|------|-------|
| zip_code_prefix | geolocation_zip_code_prefix | VARCHAR | not unique |
| latitude | geolocation_lat | DOUBLE | never null |
| longitude | geolocation_lng | DOUBLE | never null |
| city | geolocation_city | VARCHAR | |
| state | geolocation_state | VARCHAR | 27 codes |

Tests: zip_code_prefix not_null; latitude, longitude not_null. No unique test.

---

### bronze_product_category_translation

- **File:** `models/olist/bronze/bronze_product_category_translation.sql`
- **Source:** `source('olist_raw', 'product_category_name_translation')`
- **Grain:** One row per category (71 rows)

| Target Column | Source Column | Type | Notes |
|--------------|--------------|------|-------|
| product_category_name | product_category_name | VARCHAR | PK, Portuguese |
| product_category_name_english | product_category_name_english | VARCHAR | |

Tests: product_category_name unique + not_null;
product_category_name_english not_null.

---

## Intermediate Models

Location: `models/olist/silver/intermediate/`. Materialized as tables via the
silver folder config. Reference bronze only.

---

### int_geolocation_deduped

- **File:** `models/olist/silver/intermediate/int_geolocation_deduped.sql`
- **Depends on:** `ref('bronze_geolocation')`
- **Grain:** One row per zip_code_prefix (19,015 rows)
- **Purpose:** Collapse the 1M-row geolocation table to one deterministic coordinate per zip so downstream joins cannot fan out

Logic: `ROW_NUMBER() OVER (PARTITION BY zip_code_prefix ORDER BY latitude, longitude, city)` and keep row 1. Ordering makes the pick deterministic across rebuilds.

| Column | Type | Logic |
|--------|------|-------|
| zip_code_prefix | VARCHAR | partition key |
| latitude | DOUBLE | from kept row |
| longitude | DOUBLE | from kept row |
| city | VARCHAR | from kept row |
| state | VARCHAR | from kept row |
| observation_count | INTEGER | COUNT(*) over partition, kept for transparency |

Tests: zip_code_prefix unique + not_null.

---

### int_order_payments

- **File:** `models/olist/silver/intermediate/int_order_payments.sql`
- **Depends on:** `ref('bronze_order_payments')`
- **Grain:** One row per order with at least one payment (99,440 rows)
- **Purpose:** Resolve the one-to-many payment relationship to order grain per BRD rule "payment_type = most common for order"

Logic:
1. CTE `by_type`: GROUP BY order_id, payment_type with COUNT(*) AS type_count and SUM(payment_value) AS type_value.
2. CTE `ranked`: `ROW_NUMBER() OVER (PARTITION BY order_id ORDER BY type_count DESC, type_value DESC, payment_type)`; keep rank 1 as the order's payment_type.
3. CTE `totals`: GROUP BY order_id with SUM(payment_value), MAX(payment_installments), COUNT(*), COUNT(DISTINCT payment_type).
4. Join ranked to totals on order_id.

| Column | Type | Logic |
|--------|------|-------|
| order_id | VARCHAR | PK |
| payment_type | VARCHAR | modal type, tie-break by value then alpha |
| payment_installments | INTEGER | MAX(payment_installments) |
| total_payment_value | DECIMAL(12,2) | SUM(payment_value) |
| payment_count | INTEGER | COUNT(*) |
| payment_type_count | INTEGER | COUNT(DISTINCT payment_type) |

Tests: order_id unique + not_null; payment_type accepted_values (5 values);
total_payment_value expression_is_true `>= 0`.

---

## Silver Models

Rules for every silver model: reference only bronze or intermediate models via
`ref()`, never `source()`. Apply business rules here. Materialize as table.
Day arithmetic uses `dbt.datediff`.

---

### silver_orders

- **File:** `models/olist/silver/silver_orders.sql`
- **Depends on:** `ref('bronze_orders')`, `ref('bronze_customers')`, `ref('int_order_payments')`
- **Grain:** One row per order, all statuses (99,441 rows)
- **Purpose:** Order header enriched with customer identity, payment summary, and delivery performance. Retains every status so the order funnel can be analyzed.

Joins:

| Left | Right | Key | Type | Cardinality |
|------|-------|-----|------|-------------|
| bronze_orders o | bronze_customers c | o.customer_id = c.customer_id | LEFT | 1:1 (verified, zero orphans) |
| bronze_orders o | int_order_payments p | o.order_id = p.order_id | LEFT | 1:0..1 (1 order has no payment) |

Filters: none.

Derived columns:

| Column | Type | Logic | Business rule |
|--------|------|-------|---------------|
| is_delivered | BOOLEAN | order_status = 'delivered' | Valid order for revenue metrics |
| order_purchase_date | DATE | CAST(order_purchase_timestamp AS DATE) | reporting convenience |
| order_purchase_month | DATE | DATE_TRUNC('month', order_purchase_timestamp) | cohorting |
| delivery_days | INTEGER | datediff(order_purchase_timestamp, order_delivered_customer_date, day) | BRD delivery_days; NULL when not delivered |
| estimated_delivery_days | INTEGER | datediff(order_purchase_timestamp, order_estimated_delivery_date, day) | BRD |
| delivery_delay_days | INTEGER | delivery_days - estimated_delivery_days | BRD; positive = late; NULL when not delivered |
| is_on_time | BOOLEAN | CASE WHEN order_delivered_customer_date IS NULL THEN NULL ELSE order_delivered_customer_date <= order_estimated_delivery_date END | BRD on-time rule |
| is_late_delivery | BOOLEAN | CASE WHEN order_delivered_customer_date IS NULL THEN NULL ELSE order_delivered_customer_date > order_estimated_delivery_date END | BRD late rule |

Pass-through columns: order_id, customer_id, customer_unique_id,
customer_zip_code_prefix, customer_city, customer_state, order_status,
order_purchase_timestamp, order_approved_at, order_delivered_carrier_date,
order_delivered_customer_date, order_estimated_delivery_date, payment_type,
payment_installments, total_payment_value, payment_count.

Tests: order_id unique + not_null; customer_id, customer_unique_id,
customer_state, order_status not_null; order_status accepted_values (8 values);
is_delivered not_null; relationships order_id to bronze_orders.

---

### silver_order_items

- **File:** `models/olist/silver/silver_order_items.sql`
- **Depends on:** `ref('bronze_order_items')`, `ref('bronze_orders')`, `ref('bronze_customers')`, `ref('bronze_products')`, `ref('bronze_product_category_translation')`, `ref('bronze_sellers')`
- **Grain:** One row per order line item (112,650 rows)
- **Purpose:** Line items with GMV, English category, seller and customer context, and order status so gold can filter to delivered without a second join

Joins:

| Left | Right | Key | Type | Cardinality |
|------|-------|-----|------|-------------|
| bronze_order_items oi | bronze_orders o | oi.order_id = o.order_id | LEFT | many:1 (zero orphans) |
| bronze_orders o | bronze_customers c | o.customer_id = c.customer_id | LEFT | 1:1 |
| bronze_order_items oi | bronze_products p | oi.product_id = p.product_id | LEFT | many:1 (zero orphans) |
| bronze_products p | bronze_product_category_translation t | p.product_category_name = t.product_category_name | LEFT | many:1 (2 categories unmatched) |
| bronze_order_items oi | bronze_sellers s | oi.seller_id = s.seller_id | LEFT | many:1 (zero orphans) |

Filters: none.

Derived columns:

| Column | Type | Logic | Business rule |
|--------|------|-------|---------------|
| gmv | DECIMAL(12,2) | price + freight_value | BRD GMV calculation |
| product_category | VARCHAR | COALESCE(t.product_category_name_english, p.product_category_name, 'unknown') | Deviation 10 |
| is_first_item | BOOLEAN | order_item_id = 1 | BRD "from first item" rule for order-level attribution |
| is_delivered | BOOLEAN | o.order_status = 'delivered' | valid order rule |

Pass-through columns: order_item_key, order_id, order_item_id, product_id,
seller_id, seller_state, customer_id, customer_unique_id, customer_state,
order_status, order_purchase_timestamp, order_delivered_customer_date,
order_estimated_delivery_date, shipping_limit_date, price, freight_value,
product_category_name (Portuguese, kept for traceability).

Tests: order_item_key unique + not_null; order_id, product_id, seller_id,
customer_unique_id, product_category, gmv not_null; gmv expression_is_true
`>= 0`; relationships seller_id to bronze_sellers.

---

### silver_customers

- **File:** `models/olist/silver/silver_customers.sql`
- **Depends on:** `ref('bronze_customers')`, `ref('int_geolocation_deduped')`
- **Grain:** One row per customer_id (99,441 rows)
- **Purpose:** Customer records with coordinates; gold rolls this up to the person (customer_unique_id)

Joins:

| Left | Right | Key | Type | Cardinality |
|------|-------|-----|------|-------------|
| bronze_customers c | int_geolocation_deduped g | c.customer_zip_code_prefix = g.zip_code_prefix | LEFT | many:1 (278 unmatched, coordinates NULL) |

Derived columns:

| Column | Type | Logic | Business rule |
|--------|------|-------|---------------|
| has_geolocation | BOOLEAN | g.zip_code_prefix IS NOT NULL | transparency on coverage gap |

Pass-through: customer_id, customer_unique_id, customer_zip_code_prefix,
customer_city, customer_state, latitude, longitude.

Tests: customer_id unique + not_null; customer_unique_id, customer_state
not_null.

---

### silver_sellers

- **File:** `models/olist/silver/silver_sellers.sql`
- **Depends on:** `ref('bronze_sellers')`, `ref('int_geolocation_deduped')`
- **Grain:** One row per seller (3,095 rows)

Joins:

| Left | Right | Key | Type | Cardinality |
|------|-------|-----|------|-------------|
| bronze_sellers s | int_geolocation_deduped g | s.seller_zip_code_prefix = g.zip_code_prefix | LEFT | many:1 (7 unmatched) |

Derived: has_geolocation BOOLEAN as above.

Pass-through: seller_id, seller_zip_code_prefix, seller_city, seller_state,
latitude, longitude.

Tests: seller_id unique + not_null; seller_state not_null.

---

### silver_order_reviews

- **File:** `models/olist/silver/silver_order_reviews.sql`
- **Depends on:** `ref('bronze_order_reviews')`, `ref('bronze_orders')`
- **Grain:** One row per review-order pair (99,224 rows)
- **Purpose:** Reviews with sentiment classification and the delivery context of the order they rate. Added beyond the BRD so gold never reads bronze.

Joins:

| Left | Right | Key | Type | Cardinality |
|------|-------|-----|------|-------------|
| bronze_order_reviews r | bronze_orders o | r.order_id = o.order_id | LEFT | many:1 (zero orphans) |

Derived columns:

| Column | Type | Logic | Business rule |
|--------|------|-------|---------------|
| sentiment_bucket | VARCHAR | CASE WHEN review_score <= 2 THEN 'Negative' WHEN review_score = 3 THEN 'Neutral' ELSE 'Positive' END | BRD sentiment rules |
| has_comment | BOOLEAN | NULLIF(TRIM(review_comment_message), '') IS NOT NULL | Deviation 9 |
| has_title | BOOLEAN | NULLIF(TRIM(review_comment_title), '') IS NOT NULL | supplementary |
| response_time_days | INTEGER | datediff(review_creation_date, review_answer_timestamp, day) | BRD |
| delivery_delay_days | INTEGER | datediff(order_purchase_timestamp, order_delivered_customer_date, day) - datediff(order_purchase_timestamp, order_estimated_delivery_date, day) | same expression as silver_orders |
| is_late_delivery | BOOLEAN | CASE WHEN order_delivered_customer_date IS NULL THEN NULL ELSE order_delivered_customer_date > order_estimated_delivery_date END | BRD |
| review_sequence | INTEGER | ROW_NUMBER() OVER (PARTITION BY order_id ORDER BY review_creation_date, review_answer_timestamp, review_id) | lets consumers pick one review per order if needed |

Pass-through: review_order_key, review_id, order_id, customer_id,
order_status, review_score, review_comment_title, review_comment_message,
review_creation_date, review_answer_timestamp.

Tests: review_order_key unique + not_null; review_id, order_id, customer_id,
review_score not_null; sentiment_bucket accepted_values [Negative, Neutral,
Positive]; response_time_days expression_is_true `>= 0`.

---

## Gold Models

Rules for every gold model: reference only silver models via `ref()`. Every
metric matches the BRD definition or a numbered deviation above. Materialize as
table.

---

### gold_orders

- **File:** `models/olist/gold/gold_orders.sql`
- **Depends on:** `ref('silver_orders')`, `ref('silver_order_items')`
- **Grain:** One row per delivered order (96,478 rows)
- **Purpose:** Order lifecycle, delivery performance, basket size, and payment summary for delivered orders. Informs logistics SLA reviews and AOV tracking.

Logic:
1. CTE `orders`: silver_orders WHERE is_delivered.
2. CTE `item_agg`: silver_order_items GROUP BY order_id with COUNT(*), SUM(gmv), AVG(price), COUNT(DISTINCT seller_id), COUNT(DISTINCT product_category).
3. CTE `first_item`: silver_order_items WHERE is_first_item, selecting seller_id, seller_state, product_category.
4. LEFT JOIN item_agg and first_item to orders on order_id (both 1:1 at order grain; every delivered order has items).

| Column | Type | Logic | Metric definition |
|--------|------|-------|-------------------|
| order_id | VARCHAR | grain | |
| customer_id | VARCHAR | pass-through | |
| customer_unique_id | VARCHAR | pass-through | enables join to gold_customers |
| order_status | VARCHAR | pass-through, always 'delivered' | BRD key column |
| order_purchase_timestamp | TIMESTAMP | pass-through | |
| order_purchase_date | DATE | pass-through | |
| order_delivered_customer_date | TIMESTAMP | pass-through, NULL on 8 rows | |
| order_estimated_delivery_date | TIMESTAMP | pass-through | |
| delivery_days | INTEGER | pass-through | BRD |
| estimated_delivery_days | INTEGER | pass-through | BRD |
| delivery_delay_days | INTEGER | pass-through | BRD |
| is_on_time | BOOLEAN | pass-through | BRD on_time_delivery |
| total_items | INTEGER | COUNT(*) of items | BRD |
| total_gmv | DECIMAL(12,2) | SUM(gmv) | BRD gmv |
| avg_item_price | DECIMAL(12,2) | AVG(price) | BRD |
| distinct_sellers | INTEGER | COUNT(DISTINCT seller_id) | flags multi-seller orders |
| payment_type | VARCHAR | pass-through (modal) | BRD, deviation 5 |
| payment_installments | INTEGER | pass-through (max) | BRD |
| total_payment_value | DECIMAL(12,2) | pass-through | reconciliation vs gmv |
| customer_state | VARCHAR | pass-through | BRD |
| seller_id | VARCHAR | first item | attribution |
| seller_state | VARCHAR | first item | BRD "from first item" |
| primary_product_category | VARCHAR | first item | attribution |

Tests: order_id unique + not_null; customer_unique_id, total_items, total_gmv,
customer_state, seller_state not_null; total_items expression_is_true `>= 1`;
total_gmv expression_is_true `>= 0`; order_status accepted_values [delivered].
Delivery columns are intentionally nullable (8 rows).

---

### gold_customers

- **File:** `models/olist/gold/gold_customers.sql`
- **Depends on:** `ref('silver_customers')`, `ref('silver_orders')`, `ref('silver_order_items')`, `ref('silver_order_reviews')`
- **Grain:** One row per customer_unique_id (96,096 rows)
- **Purpose:** Lifetime value and repeat behavior per person. Informs retention and cohort analysis.

Logic:
1. CTE `customer_base`: silver_customers joined to silver_orders on customer_id; ROW_NUMBER() OVER (PARTITION BY customer_unique_id ORDER BY order_purchase_timestamp DESC) and keep row 1 for customer_state and customer_city.
2. CTE `order_agg`: silver_orders GROUP BY customer_unique_id with COUNT(DISTINCT order_id) all statuses, COUNT(DISTINCT CASE WHEN is_delivered THEN order_id END), MIN/MAX(order_purchase_timestamp).
3. CTE `spend_agg`: silver_order_items WHERE is_delivered GROUP BY customer_unique_id with COUNT(*) items, SUM(gmv).
4. CTE `review_agg`: silver_order_reviews joined to silver_orders on order_id GROUP BY customer_unique_id with AVG(review_score), COUNT(*).
5. LEFT JOIN all aggregates to customer_base.

| Column | Type | Logic | Metric definition |
|--------|------|-------|-------------------|
| customer_unique_id | VARCHAR | grain | deviation 2 |
| customer_state | VARCHAR | from most recent order | BRD |
| customer_city | VARCHAR | from most recent order | |
| first_order_date | DATE | MIN(order_purchase_timestamp) all statuses | BRD |
| last_order_date | DATE | MAX(order_purchase_timestamp) all statuses | BRD |
| total_orders | INTEGER | COUNT(DISTINCT order_id) all statuses | BRD |
| delivered_orders | INTEGER | COUNT(DISTINCT order_id) WHERE is_delivered | supports valid-order rule |
| total_items | INTEGER | COUNT(items) on delivered orders, COALESCE 0 | BRD |
| total_spend | DECIMAL(12,2) | SUM(gmv) on delivered orders, COALESCE 0 | BRD, valid-order rule |
| avg_order_value | DECIMAL(12,2) | total_spend / NULLIF(delivered_orders, 0) | BRD |
| is_repeat_customer | BOOLEAN | total_orders > 1 | BRD |
| avg_review_score | DECIMAL(4,2) | AVG(review_score) across this person's reviews | BRD |
| total_reviews | INTEGER | COUNT(reviews), COALESCE 0 | |
| customer_lifespan_days | INTEGER | datediff(first_order_date, last_order_date, day) | BRD |
| avg_days_between_orders | DECIMAL(10,2) | customer_lifespan_days / NULLIF(total_orders - 1, 0) | BRD; NULL for single-order customers |

Tests: customer_unique_id unique + not_null; customer_state, first_order_date,
last_order_date, total_orders, total_spend, is_repeat_customer not_null;
total_orders expression_is_true `>= 1`; total_spend expression_is_true `>= 0`;
customer_lifespan_days expression_is_true `>= 0`.

Expected checks: SUM(CASE WHEN is_repeat_customer THEN 1 END) = 2,997.

---

### gold_sellers

- **File:** `models/olist/gold/gold_sellers.sql`
- **Depends on:** `ref('silver_sellers')`, `ref('silver_order_items')`, `ref('silver_orders')`, `ref('silver_order_reviews')`
- **Grain:** One row per seller (3,095 rows)
- **Purpose:** Seller performance scorecard combining volume, revenue, delivery reliability, and review quality, with a tier for account management.

Logic:
1. CTE `activity`: silver_order_items GROUP BY seller_id with COUNT(DISTINCT order_id) all statuses, COUNT(*) items, COUNT(DISTINCT customer_unique_id), COUNT(DISTINCT product_category).
2. CTE `revenue`: silver_order_items WHERE is_delivered GROUP BY seller_id with SUM(gmv), COUNT(DISTINCT order_id) delivered_orders.
3. CTE `delivery`: DISTINCT seller_id, order_id from silver_order_items joined to silver_orders WHERE is_delivered, GROUP BY seller_id with AVG(delivery_days), AVG(CASE WHEN is_on_time THEN 1.0 ELSE 0.0 END) over rows where is_on_time IS NOT NULL. Distinct on (seller_id, order_id) first so multi-item orders are not double counted.
4. CTE `reviews`: DISTINCT seller_id, review_order_key, review_score from silver_order_items joined to silver_order_reviews on order_id, GROUP BY seller_id with AVG(review_score), COUNT(*), COUNT 5-star, COUNT 1-star.
5. LEFT JOIN all to silver_sellers. COALESCE counts and sums to 0.
6. seller_tier CASE on total_gmv and avg_review_score.

| Column | Type | Logic | Metric definition |
|--------|------|-------|-------------------|
| seller_id | VARCHAR | grain | |
| seller_state | VARCHAR | pass-through | BRD |
| seller_city | VARCHAR | pass-through | |
| total_orders | INTEGER | COUNT(DISTINCT order_id) all statuses | BRD |
| delivered_orders | INTEGER | COUNT(DISTINCT order_id) delivered | supports valid-order rule |
| total_items_sold | INTEGER | COUNT(items) all statuses | BRD |
| total_gmv | DECIMAL(12,2) | SUM(gmv) on delivered orders | BRD, valid-order rule |
| unique_customers | INTEGER | COUNT(DISTINCT customer_unique_id) | BRD |
| unique_product_categories | INTEGER | COUNT(DISTINCT product_category) | BRD |
| avg_review_score | DECIMAL(4,2) | AVG(review_score) over distinct review-order pairs touching this seller | BRD |
| total_reviews | INTEGER | COUNT(distinct review_order_key) | denominator |
| pct_5_star | DECIMAL(5,4) | five_star_reviews / NULLIF(total_reviews, 0) | deviation 4 |
| pct_1_star | DECIMAL(5,4) | one_star_reviews / NULLIF(total_reviews, 0) | deviation 4 |
| avg_delivery_days | DECIMAL(6,2) | AVG(delivery_days) over distinct delivered orders | BRD |
| on_time_delivery_rate | DECIMAL(5,4) | AVG(is_on_time as 1/0) over distinct delivered orders with a delivered date | BRD |
| seller_tier | VARCHAR | CASE WHEN total_gmv >= 10000 AND avg_review_score >= 4.0 THEN 'Gold' WHEN total_gmv >= 1000 AND avg_review_score >= 3.5 THEN 'Silver' ELSE 'Bronze' END | deviation 8 |

Tests: seller_id unique + not_null; seller_state, total_orders,
total_items_sold, total_gmv, seller_tier not_null; total_gmv
expression_is_true `>= 0`; seller_tier accepted_values [Gold, Silver, Bronze];
pct_5_star and pct_1_star accepted_range 0 to 1 (where not null);
on_time_delivery_rate accepted_range 0 to 1 (where not null).

Expected checks: 3,095 rows; 125 sellers have total_gmv = 0 (no delivered
orders); roughly 221 Gold and 1,121 Silver.

---

### gold_reviews

- **File:** `models/olist/gold/gold_reviews.sql`
- **Depends on:** `ref('silver_order_reviews')`, `ref('silver_orders')`, `ref('silver_order_items')`
- **Grain:** One row per review-order pair (99,224 rows)
- **Purpose:** Review sentiment with the product and delivery context needed to explain it. Informs seller coaching and logistics escalations.

Logic:
1. Base: silver_order_reviews.
2. LEFT JOIN silver_orders on order_id for customer_unique_id, customer_state, delivery_days.
3. LEFT JOIN silver_order_items WHERE is_first_item on order_id for product_category, seller_id, seller_state (1:1 at order grain; NULL for the 775 item-less orders).

| Column | Type | Logic | Metric definition |
|--------|------|-------|-------------------|
| review_order_key | VARCHAR | grain | deviation 1 |
| review_id | VARCHAR | pass-through | BRD |
| order_id | VARCHAR | pass-through | BRD |
| customer_id | VARCHAR | pass-through | BRD |
| customer_unique_id | VARCHAR | from silver_orders | |
| customer_state | VARCHAR | from silver_orders | |
| review_score | INTEGER | pass-through | BRD |
| sentiment_bucket | VARCHAR | pass-through | BRD |
| has_comment | BOOLEAN | pass-through | BRD, deviation 9 |
| review_creation_date | DATE | CAST(review_creation_date AS DATE) | BRD |
| response_time_days | INTEGER | pass-through | BRD |
| review_sequence | INTEGER | pass-through | dedup helper |
| order_status | VARCHAR | pass-through | context |
| product_category | VARCHAR | first item | BRD |
| seller_id | VARCHAR | first item | context |
| seller_state | VARCHAR | first item | context |
| delivery_days | INTEGER | from silver_orders | context |
| delivery_delay_days | INTEGER | pass-through | BRD |
| is_late_delivery | BOOLEAN | pass-through | BRD |

Tests: review_order_key unique + not_null; review_id, order_id, customer_id,
review_score, sentiment_bucket, has_comment not_null; sentiment_bucket
accepted_values [Negative, Neutral, Positive]; review_score accepted_values
[1, 2, 3, 4, 5]; response_time_days expression_is_true `>= 0`.

---

## Tests Summary

| Model | Test | Columns / expression |
|-------|------|----------------------|
| bronze_orders | unique, not_null | order_id |
| bronze_orders | not_null | customer_id, order_purchase_timestamp, order_estimated_delivery_date |
| bronze_orders | accepted_values | order_status: 8 values |
| bronze_order_items | unique, not_null | order_item_key |
| bronze_order_items | not_null | order_id, product_id, seller_id, price, freight_value |
| bronze_order_payments | unique, not_null | order_payment_key |
| bronze_order_payments | not_null | order_id |
| bronze_order_payments | accepted_values | payment_type: 5 values |
| bronze_order_reviews | unique, not_null | review_order_key |
| bronze_order_reviews | not_null | review_id, order_id |
| bronze_order_reviews | accepted_values | review_score: 1-5 |
| bronze_customers | unique, not_null | customer_id |
| bronze_customers | not_null | customer_unique_id, customer_state |
| bronze_sellers | unique, not_null | seller_id |
| bronze_sellers | not_null | seller_state |
| bronze_products | unique, not_null | product_id |
| bronze_geolocation | not_null | zip_code_prefix, latitude, longitude |
| bronze_product_category_translation | unique, not_null | product_category_name |
| bronze_product_category_translation | not_null | product_category_name_english |
| int_geolocation_deduped | unique, not_null | zip_code_prefix |
| int_order_payments | unique, not_null | order_id |
| int_order_payments | accepted_values | payment_type: 5 values |
| int_order_payments | expression_is_true | total_payment_value >= 0 |
| silver_orders | unique, not_null | order_id |
| silver_orders | not_null | customer_id, customer_unique_id, customer_state, order_status, is_delivered |
| silver_orders | accepted_values | order_status: 8 values |
| silver_orders | relationships | order_id to bronze_orders.order_id |
| silver_order_items | unique, not_null | order_item_key |
| silver_order_items | not_null | order_id, product_id, seller_id, customer_unique_id, product_category, gmv |
| silver_order_items | expression_is_true | gmv >= 0 |
| silver_order_items | relationships | seller_id to bronze_sellers.seller_id |
| silver_customers | unique, not_null | customer_id |
| silver_customers | not_null | customer_unique_id, customer_state |
| silver_sellers | unique, not_null | seller_id |
| silver_sellers | not_null | seller_state |
| silver_order_reviews | unique, not_null | review_order_key |
| silver_order_reviews | not_null | review_id, order_id, customer_id, review_score |
| silver_order_reviews | accepted_values | sentiment_bucket: Negative, Neutral, Positive |
| silver_order_reviews | expression_is_true | response_time_days >= 0 |
| gold_orders | unique, not_null | order_id |
| gold_orders | not_null | customer_unique_id, total_items, total_gmv, customer_state, seller_state |
| gold_orders | expression_is_true | total_items >= 1; total_gmv >= 0 |
| gold_orders | accepted_values | order_status: delivered |
| gold_customers | unique, not_null | customer_unique_id |
| gold_customers | not_null | customer_state, first_order_date, last_order_date, total_orders, total_spend, is_repeat_customer |
| gold_customers | expression_is_true | total_orders >= 1; total_spend >= 0; customer_lifespan_days >= 0 |
| gold_sellers | unique, not_null | seller_id |
| gold_sellers | not_null | seller_state, total_orders, total_items_sold, total_gmv, seller_tier |
| gold_sellers | expression_is_true | total_gmv >= 0 |
| gold_sellers | accepted_values | seller_tier: Gold, Silver, Bronze |
| gold_sellers | accepted_range | pct_5_star, pct_1_star, on_time_delivery_rate in [0, 1] |
| gold_reviews | unique, not_null | review_order_key |
| gold_reviews | not_null | review_id, order_id, customer_id, review_score, sentiment_bucket, has_comment |
| gold_reviews | accepted_values | sentiment_bucket: 3 values; review_score: 1-5 |
| gold_reviews | expression_is_true | response_time_days >= 0 |

### Row count reconciliation (run after build)

| Model | Expected rows | Source of truth |
|-------|---------------|-----------------|
| gold_orders | 96,478 | raw.orders WHERE order_status = 'delivered' |
| gold_customers | 96,096 | COUNT(DISTINCT customer_unique_id) FROM raw.customers |
| gold_sellers | 3,095 | raw.sellers (all have at least one item) |
| gold_reviews | 99,224 | raw.order_reviews (zero orphan orders) |
| silver_orders | 99,441 | raw.orders |
| silver_order_items | 112,650 | raw.order_items |
| int_geolocation_deduped | 19,015 | COUNT(DISTINCT geolocation_zip_code_prefix) |
| int_order_payments | 99,440 | COUNT(DISTINCT order_id) FROM raw.order_payments |

---

## Build Order

1. `dbt build --select tag:olist,tag:bronze` (9 views)
2. `dbt build --select path:models/olist/silver/intermediate` (2 tables)
3. `dbt build --select tag:olist,tag:silver` (5 tables plus intermediates)
4. `dbt build --select tag:olist,tag:gold` (4 tables)
5. `dbt build --select tag:olist` for the full graph; target under 60 seconds.

---

## Definition of Done

- [ ] All 9 bronze models build without errors
- [ ] Both intermediate models build without errors
- [ ] All 5 silver models build without errors
- [ ] All 4 gold models build without errors
- [ ] All tests pass (zero failures)
- [ ] Row counts match the reconciliation table above
- [ ] All columns documented in schema.yml with descriptions
- [ ] No hardcoded database or schema references (source() and ref() only)
- [ ] All SQL keywords uppercase
- [ ] All field names lowercase_with_underscores
- [ ] Day arithmetic uses dbt.datediff so models compile on Snowflake unchanged
- [ ] Full `dbt build --select tag:olist` completes in under 60 seconds on DuckDB
- [ ] Deviations 1 to 10 acknowledged by the BRD owner
- [ ] PR created with full summary and checklist complete

---

## Validation Report (2026-09-01)

Validated with /validate-spec against the live DuckDB file.

**Blockers:** none.

**Warnings:**

1. review_comment_message is NULL on 58.7% of reviews and review_comment_title on 88.3%. Both feed only boolean flags (has_comment, has_title) whose purpose is to detect the null, so this is by design, not a data defect.
2. Bronze models carry dbt_utils surrogate keys (order_item_key, order_payment_key, review_order_key). These are technical composite keys, not business logic, and exist so unique tests can run on the true grain. Acknowledged deviation from the "no calculated columns in bronze" rule.
3. Delivery metrics in gold_orders (delivery_days, delivery_delay_days, is_on_time) are nullable for the 8 delivered orders with no delivered date. Not tested for not_null on purpose.
4. review_id duplicates in source (789 ids across multiple orders) are handled by the review_order_key grain. Documented in deviation 1.

**Data quality findings:** all 9 source tables accessible with expected row counts; all bronze column names verified against information_schema; zero orphan foreign keys on all 6 relationships; join match rates 99.2% or better on every join (lowest: orders to reviews at 99.23%, customers to geolocation at 99.72%); accepted_values lists match actual distinct values for order_status, payment_type, review_score; no future dates; no negative prices or freight.

**Verdict:** APPROVED with warnings noted. Proceed with /build-bronze-models.
