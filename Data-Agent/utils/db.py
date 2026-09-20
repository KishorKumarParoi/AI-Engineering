import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()


class DatabaseUtil:
    def __init__(self, db_config):
        self.db_config = db_config
        try:
            self.connection = psycopg2.connect(**db_config)
        except Exception as e:
            print(f"Error connecting to database: {e}")
            self.connection = None

    def schema_details(self, schema_name="public"):
        cursor = None
        connection = self.connection
        try:
            if not connection:
                print("No database connection available.")
                return None

            cursor = connection.cursor()
            schema_info_context = f"Database Schema: {schema_name}\n"
            schema_info_context += "=" * 50 + "\n"

            cursor.execute(
                "SELECT table_name FROM information_schema.tables WHERE table_schema = %s ORDER BY table_name;",
                (schema_name,)
            )
            tables_list = cursor.fetchall()

            for table in tables_list:
                table_name = table[0]
                schema_info_context += f"\nTable: {table_name}\n"
                schema_info_context += "-" * 30 + "\n"

                # Adding columns data
                cursor.execute(
                    "SELECT column_name, data_type FROM information_schema.columns WHERE table_schema = %s AND table_name = %s ORDER BY ordinal_position;",
                    (schema_name, table_name)
                )
                columns_list = cursor.fetchall()

                schema_info_context += "Columns:\n"
                for column in columns_list:
                    column_name = column[0]
                    data_type = column[1]
                    schema_info_context += f"  - {column_name}: {data_type}\n"

                # Adding sample data
                cursor.execute(f"SELECT * FROM {schema_name}.{table_name} LIMIT 5;")
                sample_data = cursor.fetchall()

                schema_info_context += "\nSample Data (First 5 rows):\n"
                for row in sample_data:
                    schema_info_context += f"  {row}\n"

            return schema_info_context
        except Exception as e:
            print(f"Error getting schema details: {e}")
            return None
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()
        
    def execute_query(self, query):
        try:
            connection = self.connection 
            cursor = connection.cursor()
            cursor.execute(query)

            result = cursor.fetchall()
            connection.commit()
            return str(result)
        except Exception as e:
            print(f"Error executing query: {e}")
            return None
        finally:
            if cursor:
                cursor.close()
            if connection:
                 connection.close()
    

if __name__ == "__main__":
    obj = DatabaseUtil({
        "host": os.getenv('host') or os.getenv('POSTGRES_HOST', 'localhost'),
        "user": os.getenv('user') or os.getenv('POSTGRES_USER', 'postgres'),
        "password": os.getenv('password') or os.getenv('POSTGRES_PASSWORD', 'postgres'),
        "database": os.getenv('database') or os.getenv('POSTGRES_DB', 'data_agent_db'),
        "port": int(os.getenv('port') or os.getenv('POSTGRES_PORT', '5432'))
    })

    result = obj.schema_details("public")
    if result:
        with open("test_schema_details.txt", "w", encoding="utf-8") as f:
            f.write(result)
        print("Schema details written to test_schema_details.txt")

