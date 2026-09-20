import os
import psycopg2
from psycopg2.extras import RealDictCursor
from sqlalchemy import create_engine
from langchain_community.utilities import SQLDatabase
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB", "data_agent_db")
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
)


def get_raw_connection():
    """
    Returns a raw psycopg2 PostgreSQL connection.
    """
    return psycopg2.connect(
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        dbname=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
    )


def get_sqlalchemy_engine():
    """
    Returns a SQLAlchemy engine instance.
    """
    return create_engine(DATABASE_URL)


def get_langchain_sql_db():
    """
    Returns a LangChain SQLDatabase instance for SQL agent operations.
    """
    engine = get_sqlalchemy_engine()
    return SQLDatabase(engine=engine)


def init_db():
    """
    Reads init.sql to create database schema and seed tables.
    """
    init_sql_path = os.path.join(
        os.path.dirname(__file__), "..", "init.sql"
    )
    if os.path.exists(init_sql_path):
        conn = get_raw_connection()
        cursor = conn.cursor()
        with open(init_sql_path, "r") as f:
            sql_script = f.read()
        cursor.execute(sql_script)
        conn.commit()
        cursor.close()
        conn.close()
        print("Database initialized successfully with tables and seed data.")


def execute_query(query: str):
    """
    Executes a SQL query and returns results as a list of dictionaries.
    """
    conn = get_raw_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute(query)
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return results


def save_agent_log(state):
    """
    Saves an execution log based on the AgentSchema state.
    """
    conn = get_raw_connection()
    cursor = conn.cursor()
    insert_query = """
        INSERT INTO agent_execution_logs (
            curated_ques, prompt_query_text, is_safe, generated_sql_query, sql_query_execution_result, final_response
        ) VALUES (%s, %s, %s, %s, %s, %s);
    """
    cursor.execute(
        insert_query,
        (
            getattr(state, "curated_ques", ""),
            getattr(state, "prompt_query_text", ""),
            getattr(state, "is_safe", "NO"),
            getattr(state, "generated_sql_query", ""),
            getattr(state, "sql_query_execution_result", ""),
            getattr(state, "final_response", ""),
        ),
    )
    conn.commit()
    cursor.close()
    conn.close()


if __name__ == "__main__":
    print(f"Connecting to database URL: {DATABASE_URL}")
