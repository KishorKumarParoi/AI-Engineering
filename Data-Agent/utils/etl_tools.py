
import os
import requests
import pandas as pd

class ETLTools:
    def __init__(self):
        pass
    def extract_load(self, url: str, output_folder: str, format: str):
        """
        Extracts the dataset from the given URL and loads it into the specified folder.

        Args:
            url: The URL from which to extract the dataset.
            output_folder: The folder where the extracted dataset will be loaded.
            format: The format in which to load the dataset.
        Returns:
            str: A meesage indicating the success or failure of the application
        """

        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        output_folder = os.path.join(project_root, output_folder)

        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()

            filename = os.path.join(output_folder, f"extracted_data.{format}")
            os.makedirs(output_folder, exist_ok=True)

            df = pd.json_normalize(data)

            if format == 'csv':
                df.to_csv(filename, index=False)
            elif format == 'json':
                df.to_json(filename, orient="records", lines=True)
            elif format == 'parquet':
                df.to_parquet(filename, index=False)
            else:
                return f"Unsupported format: {format}"

            return f"Data successfully extracted and saved to {filename}"
        except Exception as e:
            raise Exception(f"Error extracting dataset: {str(e)}")

    def transform_load_context(self, file_path:str, output_folder:str, output_format:str):
        """
        Transforms the given dataframe according to the ETL requirements.

        Args:
            file_path: The path to the file to transform.
            output_folder: The folder where the transformed dataframe will be loaded.
            output_format: The format in which to load the transformed dataframe.
        Returns:
            str: A meesage indicating the success or failure of the application
        """
        file_extension = os.path.splitext(file_path)[1].lower()

        if file_extension == '.csv':
            df = pd.read_csv(file_path)
        elif file_extension == '.json':
            df = pd.read_json(file_path, lines=True)
        elif file_extension == '.parquet':
            df = pd.read_parquet(file_path)
        else:
            return f"Unsupported format: {file_extension}"

        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        output_folder = os.path.join(project_root, output_folder)

        df = df.iloc[0:3]

        top_3_rows = str(df)
        return top_3_rows
    
    def execute_code(self, code:str):
        """
        This tool executes the provided code and returns the output/
        Args:
           code(str): The code to be executed.
        Returns:
           str: The output of the executed code or an error message if execution fails.
        """

        try:
            exec(code)
            return "Code executed successfully"
        except Exception as e:
            return f"Failed to execute code: {str(e)}"


if __name__ == "__main__":
    obj = ETLTools()
    # obj.extract_load("https://pokeapi.co/api/v2/pokemon/13", "data/extract", "csv")
    path = "data/extract/extracted_data.csv"
    print(obj.transform_load_context(file_path=path, output_folder='data/transform', output_format='csv'))
    