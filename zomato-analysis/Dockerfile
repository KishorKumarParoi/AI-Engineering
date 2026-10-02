FROM astrocrpublic.azurecr.io/runtime:3.3-8

# Install dbt-snowflake in its own virtual environment to isolate dependencies from Airflow
RUN python -m venv /opt/airflow/dbt_venv && \
    /opt/airflow/dbt_venv/bin/pip install --no-cache-dir dbt-snowflake
