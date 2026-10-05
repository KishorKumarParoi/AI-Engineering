import type { NextApiRequest, NextApiResponse } from 'next';
import { exec } from 'child_process';
import path from 'path';

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  const rootDir = path.resolve(process.cwd(), '..');
  const pythonBin = path.join(rootDir, '.venv', 'bin', 'python');
  const unloadScript = path.join(rootDir, 'scripts', 'unload_snowflake_to_s3.py');

  exec(`"${pythonBin}" "${unloadScript}"`, { cwd: rootDir }, (error, stdout, stderr) => {
    if (error) {
      console.error('S3 Unload Error:', error, stderr);
      return res.status(500).json({ success: false, error: stderr || error.message });
    }

    try {
      const jsonStart = stdout.indexOf('{');
      if (jsonStart !== -1) {
        const parsed = JSON.parse(stdout.substring(jsonStart));
        return res.status(200).json({
          success: true,
          data: parsed,
          message: `Successfully unloaded ${parsed.rows_unloaded} rows to ${parsed.s3_destination}`
        });
      }
    } catch (e: any) {
      return res.status(500).json({ success: false, error: 'Failed to parse unload output: ' + e.message });
    }

    return res.status(200).json({
      success: true,
      message: 'Snowflake -> S3 data unload completed successfully.'
    });
  });
}
