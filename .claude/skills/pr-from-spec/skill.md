# pr-from-spec

## Purpose
Create a professional, complete GitHub pull request after finishing a
dbt build. This skill encodes Mammoth Growth's PR standards — branch
naming, commit format, PR template, and the due diligence checklist.
The PR is the final deliverable of every agentic build. It must be
complete enough for a senior engineer to review and approve without
asking any follow-up questions.

## When to Load This Skill
- When running /pr-from-spec
- When running /github-create-pr
- When the engineer asks to push or submit work after a build
- After all three layers (bronze, silver, gold) are built and tested

## PR Philosophy
The PR is the handoff from Claude to the human engineer. Everything
Claude did during the build must be visible, auditable, and reviewable
in the PR. A reviewer who was not present during the build should be
able to understand exactly what was built, why each decision was made,
and how to verify the output is correct.

No code reaches production without human review and approval.
Claude opens the PR. The engineer merges it.

## Pre-PR Checklist

Before creating any branch or commit, verify:

### Build Completeness
- [ ] All bronze models build without errors
- [ ] All silver models build without errors
- [ ] All gold models build without errors
- [ ] All dbt tests pass with zero failures
- [ ] dbt_show spot checks on gold models show reasonable data

### Code Quality
- [ ] All SQL keywords are UPPERCASE
- [ ] All field names are lowercase_with_underscores
- [ ] All models use source() or ref() — no hardcoded table names
- [ ] All CTEs follow the standard Mammoth template
- [ ] All tables are aliased with meaningful short names

### Documentation
- [ ] schema.yml entry exists for every new model
- [ ] Every column has a description in schema.yml
- [ ] All tests are defined in schema.yml
- [ ] sources.yml is present and correctly configured

If any item above is not complete: fix it before creating the PR.
Do not push incomplete or failing work.

## Step 1 - Gather PR Content

Before writing a single git command, collect all information needed
to write a complete PR description:

### From the Tech Spec
- Business context (2-3 sentences describing what was built and why)
- List of all models built with layer, materialization, and grain
- List of all business rules implemented
- List of all tests defined

### From the Build Session
- Any decisions made that were not in the spec
- Any discrepancies found between spec and actual data
- Any edge cases handled during the build
- Row counts for key gold models (from dbt_show)

### From git diff
Run git diff main to confirm exactly which files changed:

git diff --name-only main

List every file that will be included in the PR:
- New SQL model files
- New/updated schema.yml files
- New/updated sources.yml files
- Updated dbt_project.yml if changed
- Tech spec file if added to project_docs

## Step 2 - Create Feature Branch

### Check Current Branch
git branch --show-current

If already on a feature branch from earlier in the build: stay on it.
If on main: create a new branch now.

### Branch Naming Convention
Format: initials/use-case-name

Examples:
- sk/tpch-order-analytics
- sk/pharma-sales-effectiveness
- sk/arr-reporting-rebuild

Rules:
- Always use engineer initials (from CLAUDE.md)
- Use the use case name from the tech spec title
- Lowercase only
- Hyphens not underscores
- No dates in branch names
- Keep it short but descriptive (3-5 words max)

### Create the Branch
git checkout -b sk/use-case-name

If branch already exists from earlier:
git checkout sk/use-case-name

## Step 3 - Stage and Commit All Changes

### Stage All New and Modified Files
git add -A

### Review What Will Be Committed
git status

Confirm the file list matches what was built. If unexpected files
appear: investigate before committing.

### Write the Commit Message
Follow this format exactly:

feat: build [use-case-name] bronze/silver/gold pipeline

Models built:
- bronze_model_1 (view) — raw [source] data
- bronze_model_2 (view) — raw [source] data
- silver_model_1 (table) — cleaned and joined [entity]
- gold_model_1 (table) — [business metric] by [grain]

Tests: [N] passing, 0 failing
Source: [database.schema]

### Commit
git commit -m "feat: build [use-case-name] pipeline

Models built:
- bronze_orders (view)
- bronze_lineitem (view)
- silver_orders (table)
- gold_revenue_by_segment (table)

Tests: 24 passing, 0 failing
Source: SNOWFLAKE_SAMPLE_DATA.TPCH_SF10"

## Step 4 - Push Branch to GitHub

git push origin sk/use-case-name

If the branch does not exist on remote yet:
git push --set-upstream origin sk/use-case-name

Confirm the push succeeded before proceeding to PR creation.

## Step 5 - Create the GitHub PR

Use the GitHub CLI to create the PR:

gh pr create \
  --title "[title]" \
  --body "[body from template below]" \
  --base main \
  --head sk/use-case-name

### PR Title Format
[Use Case Name] — Bronze/Silver/Gold Pipeline

Examples:
- TPCH Order Analytics — Bronze/Silver/Gold Pipeline
- Pharma Sales Effectiveness — Bronze/Silver/Gold Pipeline
- ARR Reporting Rebuild — Bronze/Silver/Gold Pipeline

## PR Body Template

Fill in every section of this template. Do not leave any section empty.
Do not use placeholder text. Every item must reflect the actual build.

---

## Summary

[2-3 sentences describing what was built and what business question
it answers. Written for a non-technical reviewer.]

Example:
This PR builds a complete order analytics pipeline using the Snowflake
TPCH sample dataset. The pipeline produces revenue and performance
metrics by customer segment, supplier nation, and part type, enabling
the business to identify which segments and suppliers drive the most
revenue and which have the highest return rates.

---

## Business Requirements Addressed

| Requirement | Model | Status |
|-------------|-------|--------|
| Revenue by customer segment | gold_revenue_by_segment | Done |
| Revenue by supplier nation | gold_revenue_by_supplier_nation | Done |
| Revenue by part type | gold_revenue_by_part_type | Done |
| Return rate analysis | gold_revenue_by_segment | Done |
| Late shipment rate | gold_revenue_by_supplier_nation | Done |

---

## Models Built

### Bronze Layer (views — raw source data, no business logic)
| Model | Source Table | Grain | Columns |
|-------|-------------|-------|---------|
| bronze_orders | TPCH_SF10.ORDERS | One row per order | 8 |
| bronze_lineitem | TPCH_SF10.LINEITEM | One row per line item | 15 |
| bronze_customer | TPCH_SF10.CUSTOMER | One row per customer | 8 |
| bronze_supplier | TPCH_SF10.SUPPLIER | One row per supplier | 7 |
| bronze_nation | TPCH_SF10.NATION | One row per nation | 4 |
| bronze_part | TPCH_SF10.PART | One row per part | 9 |

### Silver Layer (tables — cleaned, conformed, joined)
| Model | Depends On | Grain | Key Transformations |
|-------|-----------|-------|---------------------|
| silver_orders | bronze_orders, bronze_customer, bronze_nation | One row per order | Customer and nation enrichment |
| silver_lineitem | bronze_lineitem, bronze_part, bronze_supplier, bronze_nation | One row per line item | Part, supplier, nation enrichment; discounted_price and net_price calculated; is_returned and is_late_shipment derived |

### Gold Layer (tables — business-facing metrics)
| Model | Depends On | Grain | Metrics |
|-------|-----------|-------|---------|
| gold_revenue_by_segment | silver_orders, silver_lineitem | One row per market segment | total_orders, total_revenue, avg_order_value, total_items_sold, return_rate_pct |
| gold_revenue_by_supplier_nation | silver_lineitem | One row per supplier nation | total_revenue, total_quantity, total_line_items, avg_discount, late_shipment_rate_pct |
| gold_revenue_by_part_type | silver_lineitem | One row per part type | total_revenue, total_quantity, total_line_items, avg_discount, return_rate_pct |

---

## Tests

| Model | Tests Defined | Tests Passing |
|-------|--------------|---------------|
| bronze_orders | 4 | 4 |
| bronze_lineitem | 5 | 5 |
| bronze_customer | 4 | 4 |
| bronze_supplier | 2 | 2 |
| bronze_nation | 2 | 2 |
| bronze_part | 2 | 2 |
| silver_orders | 3 | 3 |
| silver_lineitem | 4 | 4 |
| gold_revenue_by_segment | 2 | 2 |
| gold_revenue_by_supplier_nation | 2 | 2 |
| gold_revenue_by_part_type | 2 | 2 |
| **TOTAL** | **32** | **32** |

---

## Key Decisions and Notes

[Document any decisions made during the build that were not in the spec,
any discrepancies found, or any edge cases handled. Be specific.]

Examples:
- bronze_lineitem: TPCH uses L_ prefix on all columns (e.g. L_ORDERKEY).
  All prefixes removed in bronze rename step.
- silver_lineitem: discounted_price calculated as extended_price * (1 - discount).
  net_price calculated as discounted_price * (1 + tax).
- gold models: return_rate_pct uses NULLIF to prevent divide-by-zero on
  segments with no line items.

---

## Data Profile Summary

| Source Table | Row Count | Key Finding |
|-------------|-----------|-------------|
| ORDERS | 15,000,000 | Clean PK, no duplicates |
| LINEITEM | 60,037,902 | ~4 line items per order avg |
| CUSTOMER | 1,500,000 | 5 market segments, balanced |
| SUPPLIER | 100,000 | 25 nations represented |
| NATION | 25 | Complete reference table |
| PART | 2,000,000 | 5 part types |

---

## Due Diligence Checklist

### Build Quality
- [ ] All bronze models build without errors
- [ ] All silver models build without errors
- [ ] All gold models build without errors
- [ ] All [N] tests pass with zero failures
- [ ] No hardcoded database or schema references in any model
- [ ] All models use source() or ref() for all table references

### Code Standards
- [ ] All SQL keywords are UPPERCASE
- [ ] All field names are lowercase_with_underscores
- [ ] All models follow the standard CTE template
- [ ] All tables aliased with meaningful short names
- [ ] Commas at start of each new column line throughout

### Documentation
- [ ] schema.yml entry exists for every new model
- [ ] Every column has a description in schema.yml
- [ ] All tests defined in schema.yml
- [ ] sources.yml present and correctly configured
- [ ] Model descriptions explain what each model does in plain English

### Architecture
- [ ] Bronze models contain no business logic
- [ ] Silver models reference only bronze via ref()
- [ ] Gold models reference only silver via ref()
- [ ] No gold model references bronze directly
- [ ] Medallion architecture layers are respected throughout

### Data Quality
- [ ] dbt_show spot check on each gold model shows reasonable data
- [ ] Row counts are in expected range for the data scale
- [ ] No unexpected nulls in critical columns
- [ ] Metric values are reasonable for the business context

---

## How to Review This PR

1. Pull the branch locally: git checkout sk/use-case-name
2. Run dbt build --select tag:[project_tag] to confirm all tests pass
3. Run dbt docs serve to view the lineage DAG
4. Query the gold models to spot-check metric values
5. Review SQL files for code quality and business logic correctness
6. Approve and merge when satisfied

---

## Step 6 - Verify the PR

After creating the PR:
1. Open the PR URL in the browser
2. Confirm the title is correct
3. Confirm all sections of the body are filled in
4. Confirm the file changes tab shows exactly the right files
5. Confirm no sensitive data (credentials, tokens) is in any file

Report the PR URL to the engineer:
PR created: https://github.com/[org]/[repo]/pull/[number]

## Post-PR Actions

After the PR is created and reported:
1. Do NOT make any further changes to the branch without engineer instruction
2. If the engineer requests changes: make them on the same branch and push
3. If tests fail in CI: investigate and fix on the same branch
4. Do NOT merge the PR — only the engineer merges

## Common PR Mistakes to Avoid

Never include in a PR:
- .env files or any file containing credentials
- dbt_cloud.yml or any authentication files
- .mcp.json if it contains tokens (use .gitignore)
- target/ folder contents
- dbt_packages/ folder contents
- Any file listed in .gitignore

Always verify .gitignore is working before pushing:
git status

Confirm target/, dbt_packages/, .env, and .mcp.json do not appear
in the staged files list.
