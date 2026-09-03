{%- macro generate_schema_name(custom_schema_name, node) -%}

    {%- set default_schema = target.schema -%}

    {%- if custom_schema_name is none -%}

        {{ default_schema }}

    {%- elif target.name == 'prod' -%}

        {#- In production: use the custom schema name exactly as defined -#}
        {#- Results in: tpch_sf10_bronze, pharma_sales_gold, etc. -#}
        {{ custom_schema_name | trim }}

    {%- else -%}

        {#- In dev: prefix with target schema to avoid collisions -#}
        {#- Results in: MAMMOTH_SCHEMA_tpch_sf10_bronze, etc. -#}
        {{ default_schema }}_{{ custom_schema_name | trim }}

    {%- endif -%}

{%- endmacro -%}