import sys
import os
# pyrefly: ignore [missing-import]
from langchain_core.messages import HumanMessage, AIMessage

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.db import DatabaseUtil
from utils.llm_pick import pick_llm
from models.schema import AgentSchema, JudgeSchema
# pyrefly: ignore [missing-import]
from langgraph.graph import StateGraph, START, END 
from langchain.tools import tool
from utils.etl_tools import ETLTools

# ETL Agent
@tool 
def extract_load_tool(url:str, output_folder: str, format: str) -> str:
    """
    Extracts the dataset from the given URL and loads it into the specified folder.

    Args:
        url: The URL from which to extract the dataset.
        output_folder: The folder where the extracted dataset will be loaded.
        format: The format in which to load the dataset.
    Returns:
        str: A meesage indicating the success or failure of the application
    """
    try:
        etl_tools = ETLTools()
        return etl_tools.extract_load(url, output_folder, format)
    except Exception as e:
        return f"Failed to extract dataset: {str(e)}"

@tool
def transform_load_context_tool(file_path:str, output_folder:str, output_format:str) -> str:
    """
    Transforms the given dataframe according to the ETL requirements.

    Args:
        file_path: The path to the file to transform.
        output_folder: The folder where the transformed dataframe will be loaded.
        output_format: The format in which to load the transformed dataframe.
    Returns:
        str: A meesage indicating the success or failure of the application
    """
    try:
        etl_tools = ETLTools()
        top_3_rows = etl_tools.transform_load_context(file_path, output_folder, output_format)
        llm = pick_llm("low")

        prompt = f"""
        You are an expert data engineer and analyst. Your task is to examine 
        the following top 3 rows of the dataset and suggest Python code to clean and normalize the data.

        Top 3 rows of the dataset:
        {top_3_rows}

        Please provide Python code to clean and normalize the dataset.
        """
        response = llm.invoke(prompt)
        return response.content
    except Exception as e:
        return f"Failed to transform dataset: {str(e)}"

@tool
def execute_code_tool(code:str) -> str:
    """
    Executes the provided code and returns the output.

    Args:
        code: The code to be executed.
    Returns:
        str: The output of the executed code or an error message if execution fails.
    """
    try:
        etl_tools = ETLTools()
        return etl_tools.execute_code(code)
    except Exception as e:
        return f"Failed to execute code: {str(e)}"