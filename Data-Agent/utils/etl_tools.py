import io
import os
import sys
import traceback
from typing import Optional
import pandas as pd
import requests


class ETLTools:
    def __init__(self, project_root: Optional[str] = None):
        self.project_root = project_root or os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..")
        )

    def _resolve_path(self, path: str) -> str:
        """Resolves relative paths against the project root."""
        if os.path.isabs(path):
            return path
        return os.path.normpath(os.path.join(self.project_root, path))

    def extract_load(self, url: str, output_folder: str, format: str) -> str:
        """
        Extracts dataset from given URL (REST API / JSON / CSV) and saves it to output folder.

        Args:
            url (str): The HTTP URL to extract from.
            output_folder (str): Directory or file destination.
            format (str): 'csv', 'json', or 'parquet'.

        Returns:
            str: Status message with destination path.
        """
        try:
            format = format.lower().strip().replace(".", "")
            resolved_output = self._resolve_path(output_folder)

            # Check if output_folder is a specific file or a directory
            if resolved_output.endswith(f".{format}"):
                dest_file = resolved_output
                dest_dir = os.path.dirname(dest_file)
            else:
                dest_dir = resolved_output
                dest_file = os.path.join(dest_dir, f"extracted_data.{format}")

            os.makedirs(dest_dir, exist_ok=True)

            response = requests.get(url, timeout=30)
            response.raise_for_status()

            # Attempt JSON parsing; fallback to CSV if text
            try:
                data = response.json()
                if isinstance(data, list):
                    df = pd.json_normalize(data)
                elif isinstance(data, dict):
                    # Check if results are nested under keys like 'results', 'data', 'items'
                    for key in ["results", "data", "items"]:
                        if key in data and isinstance(data[key], list):
                            df = pd.json_normalize(data[key])
                            break
                    else:
                        df = pd.json_normalize([data])
                else:
                    df = pd.DataFrame([data])
            except ValueError:
                # Text/CSV response
                df = pd.read_csv(io.StringIO(response.text))

            if format == "csv":
                df.to_csv(dest_file, index=False)
            elif format == "json":
                df.to_json(dest_file, orient="records", indent=2)
            elif format == "parquet":
                df.to_parquet(dest_file, index=False)
            else:
                return f"Unsupported format: {format}. Supported: csv, json, parquet."

            return f"Data successfully extracted ({len(df)} records, {len(df.columns)} columns) and saved to {dest_file}"
        except Exception as e:
            return f"Failed to extract dataset: {str(e)}"

    def transform_load_context(self, file_path: str, output_folder: str, output_format: str) -> str:
        """
        Inspects the source file and generates preview context (schema, shape, first 3 rows).

        Args:
            file_path (str): Path to input data file.
            output_folder (str): Target output directory.
            output_format (str): Target file format.

        Returns:
            str: Data context summary.
        """
        try:
            resolved_path = self._resolve_path(file_path)
            if not os.path.exists(resolved_path):
                return f"Error: Source file does not exist at {resolved_path}"

            ext = os.path.splitext(resolved_path)[1].lower()
            if ext == ".csv":
                df = pd.read_csv(resolved_path)
            elif ext == ".json":
                try:
                    df = pd.read_json(resolved_path, lines=True)
                except Exception:
                    df = pd.read_json(resolved_path)
            elif ext == ".parquet":
                df = pd.read_parquet(resolved_path)
            else:
                return f"Unsupported file extension: {ext}"

            summary = [
                f"File: {resolved_path}",
                f"Shape: {df.shape[0]} rows x {df.shape[1]} columns",
                f"Columns & Types:\n" + "\n".join([f"  - {col}: {dtype}" for col, dtype in df.dtypes.items()]),
                f"\nFirst 3 rows:\n{df.head(3).to_string()}"
            ]
            return "\n".join(summary)
        except Exception as e:
            return f"Error generating transform context: {str(e)}"

    def execute_code(self, code: str) -> str:
        """
        Executes generated Python ETL code in a controlled context, capturing stdout.

        Args:
            code (str): Python script to execute.

        Returns:
            str: Execution summary or error traceback.
        """
        old_stdout = sys.stdout
        redirected_output = io.StringIO()
        sys.stdout = redirected_output

        execution_namespace = {
            "pd": pd,
            "pandas": pd,
            "requests": requests,
            "os": os,
            "sys": sys,
            "io": io,
            "project_root": self.project_root,
        }

        # Change cwd to project_root during execution for reliable relative paths
        orig_cwd = os.getcwd()
        try:
            os.chdir(self.project_root)
            exec(code, execution_namespace)
            output = redirected_output.getvalue()
            return f"Code executed successfully.\nOutput: {output.strip() if output else 'No output'}"
        except Exception as e:
            err_trace = traceback.format_exc()
            return f"Execution error: {str(e)}\nTraceback:\n{err_trace}"
        finally:
            sys.stdout = old_stdout
            os.chdir(orig_cwd)


if __name__ == "__main__":
    tools = ETLTools()
    path = "data/extract/extracted_data.csv"
    print(tools.transform_load_context(path, "data/transform", "csv"))