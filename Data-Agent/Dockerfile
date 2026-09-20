# Use official PostgreSQL 16 Alpine image
FROM postgres:16-alpine

# Environment variables
ENV POSTGRES_DB=data_agent_db
ENV POSTGRES_USER=postgres
ENV POSTGRES_PASSWORD=postgres

# Copy initialization script to docker-entrypoint-initdb.d
# Scripts in this directory run automatically on database creation
COPY init.sql /docker-entrypoint-initdb.d/

EXPOSE 5432
