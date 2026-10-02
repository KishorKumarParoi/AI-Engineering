FROM astrocrpublic.azurecr.io/runtime:3.3-8

# Switch to root to grant permissions on /opt/airflow, then switch back to astro user
USER root
RUN mkdir -p /opt/airflow && chown -R astro:0 /opt/airflow
USER astro

# Install dbt-snowflake in its own virtual environment to isolate dependencies from Airflow
RUN python -m venv /opt/airflow/dbt_venv && \
    /opt/airflow/dbt_venv/bin/pip install --no-cache-dir dbt-snowflake
