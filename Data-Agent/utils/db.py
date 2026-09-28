import os
from typing import Any, Dict, List, Optional
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()


class DatabaseUtil:
    def __init__(self, db_config: Optional[Dict[str, Any]] = None):
        self.db_config = db_config or {
            "host": os.getenv("POSTGRES_HOST") or os.getenv("host", "localhost"),
            "user": os.getenv("POSTGRES_USER") or os.getenv("user", "postgres"),
            "password": os.getenv("POSTGRES_PASSWORD") or os.getenv("password", "postgres"),
            "database": os.getenv("POSTGRES_DB") or os.getenv("database", "data_agent_db"),
            "port": int(os.getenv("POSTGRES_PORT") or os.getenv("port", "5432")),
        }
        self.connection = None
        self._connect()

    def _connect(self):
        try:
            self.connection = psycopg2.connect(**self.db_config)
        except Exception as e:
            print(f"Error connecting to database: {e}")
            self.connection = None

    def get_connection(self):
        """Ensures an active connection is returned, reconnecting if closed."""
        if self.connection is None or self.connection.closed != 0:
            self._connect()
        return self.connection

    def schema_details(self, schema_name: str = "public") -> Optional[str]:
        """Introspects tables, columns, data types, and top 5 sample rows."""
        cursor = None
        try:
            conn = self.get_connection()
            if not conn:
                return "Error: Unable to connect to the database."

            cursor = conn.cursor()
            schema_info_context = f"Database Schema: {schema_name}\n"
            schema_info_context += "=" * 50 + "\n"

            cursor.execute(
                "SELECT table_name FROM information_schema.tables WHERE table_schema = %s ORDER BY table_name;",
                (schema_name,),
            )
            tables_list = cursor.fetchall()

            for table in tables_list:
                table_name = table[0]
                schema_info_context += f"\nTable: {table_name}\n"
                schema_info_context += "-" * 30 + "\n"

                # Fetch column details
                cursor.execute(
                    "SELECT column_name, data_type FROM information_schema.columns "
                    "WHERE table_schema = %s AND table_name = %s ORDER BY ordinal_position;",
                    (schema_name, table_name),
                )
                columns_list = cursor.fetchall()

                schema_info_context += "Columns:\n"
                for column in columns_list:
                    schema_info_context += f"  - {column[0]}: {column[1]}\n"

                # Fetch sample rows
                cursor.execute(f"SELECT * FROM {schema_name}.{table_name} LIMIT 5;")
                col_names = [desc[0] for desc in cursor.description]
                sample_rows = cursor.fetchall()

                schema_info_context += f"\nSample Data (First 5 rows, columns: {', '.join(col_names)}):\n"
                for row in sample_rows:
                    schema_info_context += f"  {row}\n"

            return schema_info_context
        except Exception as e:
            print(f"Error getting schema details: {e}")
            return f"Error introspecting schema: {str(e)}"
        finally:
            if cursor:
                cursor.close()

    def execute_query(self, query: str) -> str:
        """Executes a SQL query and returns results formatted with column names."""
        cursor = None
        try:
            conn = self.get_connection()
            if not conn:
                return "Error: Database connection not available."

            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute(query)

            # Check if query returned rows (e.g. SELECT)
            if cursor.description:
                rows = cursor.fetchall()
                conn.commit()
                if not rows:
                    return "Query executed successfully. Result: 0 rows returned."
                # Format as structured records string
                records = [dict(r) for r in rows]
                return str(records)
            else:
                conn.commit()
                return f"Query executed successfully. Rows affected: {cursor.rowcount}"
        except Exception as e:
            if self.connection and not self.connection.closed:
                self.connection.rollback()
            return f"Error executing query: {str(e)}"
        finally:
            if cursor:
                cursor.close()

    def close(self):
        """Explicitly close database connection if desired."""
        if self.connection and not self.connection.closed:
            self.connection.close()


if __name__ == "__main__":
    db = DatabaseUtil()
    result = db.schema_details("public")
    if result:
        print("Schema details successfully extracted.")
    query_result = db.execute_query("SELECT count(*) as total_users FROM users;")
    print("Query Result:", query_result)
    db.close()
