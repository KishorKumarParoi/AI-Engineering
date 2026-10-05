import type { NextApiRequest, NextApiResponse } from 'next';
import { exec } from 'child_process';
import path from 'path';

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse<{ success: boolean; data?: any; message: string; error?: string }>
) {
  const rootDir = path.resolve(process.cwd(), '..');
  const syncScript = path.join(rootDir, 'scripts', 'run_airflow_kafka_db_sync.py');
  const pythonBin = path.join(rootDir, '.venv', 'bin', 'python');

  exec(`"${pythonBin}" "${syncScript}"`, { cwd: rootDir }, (error, stdout, stderr) => {
    if (error) {
      console.error('Error executing Airflow sync script:', error, stderr);
      return res.status(500).json({
        success: false,
        message: 'Failed to execute Airflow Kafka database sync',
        error: stderr || error.message
      });
    }

    try {
      // Find JSON block in output
      const jsonStart = stdout.indexOf('{');
      if (jsonStart !== -1) {
        const parsed = JSON.parse(stdout.substring(jsonStart));
        return res.status(200).json({
          success: true,
          data: parsed,
          message: `Airflow Cronjob Synced: ${parsed.rows_ingested || 0} events merged into Snowflake ZOMATO.RAW.KAFKA_ORDER_EVENTS.`
        });
      }
    } catch {
      // Fallback
    }

    return res.status(200).json({
      success: true,
      message: 'Airflow Kafka-to-Snowflake database synchronization completed successfully.'
    });
  });
}
