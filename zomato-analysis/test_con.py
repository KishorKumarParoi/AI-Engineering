uv run --with snowflake-connector-python --with python-dotenv python -c "
import os, snowflake.connector
from dotenv import load_dotenv

load_dotenv()

print('Connecting to Snowflake...')
conn = snowflake.connector.connect(
    user=os.getenv('SNOWFLAKE_USERNAME'),
    password=os.getenv('SNOWFLAKE_PASSWORD'),
    account=os.getenv('SNOWFLAKE_ACCOUNT'),
    role='ACCOUNTADMIN',
    warehouse='ZOMATO_WH'
)

cur = conn.cursor()

# 1. Test Snowflake Session
cur.execute('SELECT CURRENT_USER(), CURRENT_ROLE(), CURRENT_REGION(), CURRENT_WAREHOUSE();')
user, role, region, wh = cur.fetchone()
print(f' Snowflake Connected! User: {user} | Role: {role} | Region: {region} | Warehouse: {wh}')

# 2. Test AWS S3 Stage
print('\nChecking S3 Stage files...')
cur.execute('LIST @ZOMATO.RAW.ZOMATO_RAW_STAGE;')
files = cur.fetchall()

print(f' S3 Integration Working! Found {len(files)} files:')
for f in files:
    print(f'   - {f[0]} ({round(f[1]/1024/1024, 2)} MB)')

cur.close()
conn.close()
"

