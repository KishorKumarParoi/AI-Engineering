import type { NextApiRequest, NextApiResponse } from 'next';
import { exec } from 'child_process';
import path from 'path';

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  const rootDir = path.resolve(process.cwd(), '..');
  const pythonBin = path.join(rootDir, '.venv', 'bin', 'python');
  
  // Python query script
  const pyCode = `
import os, json, snowflake.connector
from dotenv import load_dotenv
load_dotenv()

user = os.getenv('SNOWFLAKE_USERNAME') or os.getenv('SNOWFLAKE_USER')
pwd = os.getenv('SNOWFLAKE_PASSWORD')
account = os.getenv('SNOWFLAKE_ACCOUNT')
wh = os.getenv('SNOWFLAKE_WAREHOUSE', 'ZOMATO_WH')
db = os.getenv('SNOWFLAKE_DATABASE', 'ZOMATO')
schema = os.getenv('SNOWFLAKE_SCHEMA', 'RAW')

ctx = snowflake.connector.connect(
    user=user, password=pwd, account=account, warehouse=wh, database=db, schema=schema
)
cs = ctx.cursor()

cs.execute("""
    SELECT 
        COUNT(*) as total_orders,
        COUNT(DISTINCT restaurant_name) as distinct_restaurants,
        COUNT(DISTINCT cuisine) as distinct_cuisines,
        COUNT(DISTINCT city) as distinct_cities,
        SUM(order_amount) as total_gmv,
        MAX(ingested_at) as latest_sync
    FROM ZOMATO.RAW.KAFKA_ORDER_EVENTS;
""")
r = cs.fetchone()

cs.execute("""
    SELECT ORDER_ID, RESTAURANT_NAME, FOOD_NAME, CUISINE, CITY, ORDER_AMOUNT, ORDER_STATUS, INGESTED_AT
    FROM ZOMATO.RAW.KAFKA_ORDER_EVENTS
    ORDER BY INGESTED_AT DESC
    LIMIT 6;
""")
recent = []
for row in cs.fetchall():
    recent.append({
        "order_id": row[0],
        "restaurant_name": row[1],
        "food_name": row[2],
        "cuisine": row[3],
        "city": row[4],
        "order_amount": float(row[5]) if row[5] else 0.0,
        "order_status": row[6],
        "ingested_at": str(row[7])
    })

cs.close()
ctx.close()

result = {
    "total_orders": r[0],
    "distinct_restaurants": r[1],
    "distinct_cuisines": r[2],
    "distinct_cities": r[3],
    "total_gmv": float(r[4]) if r[4] else 0.0,
    "latest_sync": str(r[5]) if r[5] else None,
    "recent_orders": recent
}
print(json.dumps(result))
`;

  exec(`"${pythonBin}" -c "${pyCode.replace(/"/g, '\\"')}"`, { cwd: rootDir }, (error, stdout, stderr) => {
    if (error) {
      console.error('Check DB sync error:', error, stderr);
      return res.status(500).json({ success: false, error: stderr || error.message });
    }

    try {
      const jsonStart = stdout.indexOf('{');
      if (jsonStart !== -1) {
        const parsed = JSON.parse(stdout.substring(jsonStart));
        return res.status(200).json({ success: true, data: parsed });
      }
    } catch (e: any) {
      return res.status(500).json({ success: false, error: 'Failed to parse sync output: ' + e.message });
    }

    return res.status(200).json({ success: true, message: 'Verified' });
  });
}
