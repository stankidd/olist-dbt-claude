---
description: Convert a Business Requirements Document into a full Technical Specification
allowed-tools: Read(*), Edit(*), mcp__dbt__dbt_show
---

# /tech-spec-plan

Transform a Business Requirements Document (BRD) or Business Use Case into
a complete Technical Specification ready for agentic implementation.

## Usage
/tech-spec-plan $ARGUMENTS

Where $ARGUMENTS is the path to the BRD or Business Use Case document.

## Load Skill
Read and follow: skills/tech-spec-plan/skill.md

## Steps

1. **Read the BRD**
   - Open $ARGUMENTS
   - Extract: metrics defined, data sources, grain, business rules

2. **Explore source data**
   For each data source listed:
   - Use dbt show to preview the table
   - Confirm column names and data types
   - Note any data quality issues

3. **Design the Bronze layer**
   For each source table:
   - Define model name (bronze_[source_table])
   - List all columns with source name -> target name mapping
   - Note any JSON flattening needed

4. **Design the Silver layer**
   - Identify any intermediate/mapping models needed
   - For each silver model: define joins, filters, business rules
   - Specify grain for each model

5. **Design the Gold layer**
   - Define final analytical models
   - Specify all metrics with exact SQL logic
   - Define grain and materialization

6. **Write the Tech Spec**
   Save to plans/tech-spec-[use-case].md using the template from:
   .claude/templates/tech-spec-template.md

7. **Validate**
   Run /validate-spec on the output before handing to build commands.
