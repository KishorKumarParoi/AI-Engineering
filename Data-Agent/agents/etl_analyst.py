import os
import re
import sys
from typing import List

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from langchain.tools import tool
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langgraph.graph import END, START, StateGraph
from models.schema import ETLAgentSchema
from utils.etl_tools import ETLTools
from utils.llm_pick import pick_llm


@tool
def extract_load_tool(url: str, output_folder: str = "data/extract", format: str = "csv") -> str:
    """
    Extracts a dataset from an HTTP URL or REST API and saves it into the specified folder or file.

    Args:
        url (str): The HTTP URL or API endpoint to extract data from.
        output_folder (str): Directory or file path to store the data (default: 'data/extract').
        format (str): Destination format: 'csv', 'json', or 'parquet' (default: 'csv').

    Returns:
        str: Status message with destination path and record count.
    """
    try:
        etl_tools = ETLTools()
        return etl_tools.extract_load(url, output_folder, format)
    except Exception as e:
        return f"Failed to extract dataset: {str(e)}"


@tool
def transform_load_tool(
    file_path: str,
    output_folder: str = "data/transform",
    output_format: str = "csv",
    user_question: str = ""
) -> str:
    """
    Inspects a source dataset, writes custom Pandas code according to user instructions,
    executes the code, and saves the transformed result to disk.

    Args:
        file_path (str): Path to the source file to transform (CSV, JSON, or Parquet).
        output_folder (str): Destination folder or full file path (default: 'data/transform').
        output_format (str): Destination format: 'csv', 'json', or 'parquet' (default: 'csv').
        user_question (str): The specific transformation/filtering instruction.

    Returns:
        str: Execution status and path of transformed file.
    """
    try:
        etl_tools = ETLTools()
        context = etl_tools.transform_load_context(file_path, output_folder, output_format)
        llm = pick_llm("low")

        # Determine target file path
        if output_folder.endswith(f".{output_format}"):
            target_file = output_folder
        else:
            file_match = re.search(r"['\"]([^'\"]+\." + re.escape(output_format) + r")['\"]", user_question)
            if file_match and ("save" in user_question.lower() or "to" in user_question.lower()):
                target_file = file_match.group(1)
            else:
                target_file = os.path.join(output_folder, f"transformed_data.{output_format}")

        resolved_target = etl_tools._resolve_path(target_file)
        resolved_source = etl_tools._resolve_path(file_path)
        os.makedirs(os.path.dirname(resolved_target), exist_ok=True)

        prompt = f"""You are an expert Data Engineer. Write clean, robust, executable Python Pandas code to transform data.
Output pure Python code ONLY. Do not include markdown formatting, backticks, or explanatory text.

Source file path: '{resolved_source}'
Target destination file path: '{resolved_target}'
Target format: {output_format}

User Transformation Requirement:
{user_question}

Data Preview:
{context}

Requirements:
1. Load dataset with pandas (e.g. pd.read_{output_format if output_format != 'parquet' else 'parquet'} or matching extension).
2. Perform the exact filtering / transformation requested.
3. Save resulting DataFrame to '{resolved_target}' without index (e.g. df.to_{output_format}('{resolved_target}', index=False)).
"""
        response = llm.invoke(prompt).content.strip()

        # Clean code block delimiters if present
        pandas_code = response
        if "```" in pandas_code:
            parts = pandas_code.split("```")
            for part in parts:
                cleaned = part.strip()
                if cleaned.startswith("python"):
                    cleaned = cleaned[6:].strip()
                if any(kw in cleaned for kw in ["import pandas", "pd.read_", "df.to_"]):
                    pandas_code = cleaned
                    break

        print("\n--- [ETL Analyst] Generated Pandas Code ---")
        print(pandas_code)
        print("-------------------------------------------\n")

        exec_result = etl_tools.execute_code(pandas_code)

        if os.path.exists(resolved_target):
            return f"Success: Transformed dataset saved to '{resolved_target}'. Execution summary: {exec_result}"
        else:
            return f"Code executed ({exec_result}), but expected output file '{resolved_target}' was not created."

    except Exception as e:
        return f"Failed to transform dataset: {str(e)}"


@tool
def execute_code_tool(code: str) -> str:
    """
    Executes arbitrary Python code in the data processing workspace.

    Args:
        code (str): Python script to execute.

    Returns:
        str: Standard output or error traceback.
    """
    try:
        etl_tools = ETLTools()
        return etl_tools.execute_code(code)
    except Exception as e:
        return f"Failed to execute code: {str(e)}"


# Tool binding
tools = [extract_load_tool, transform_load_tool, execute_code_tool]
tools_by_name = {tool.name: tool for tool in tools}

llm = pick_llm("medium")
llm_with_tools = llm.bind_tools(tools)


# Subgraph Nodes
def llm_node(state: ETLAgentSchema) -> dict:
    """Evaluates conversation and invokes tools or formulates the final answer."""
    system_message = SystemMessage(
        content=(
            "You are an expert Data Engineer ETL Agent equipped with tools for:\n"
            "1. extract_load_tool: Fetching datasets from REST APIs / URLs and persisting to disk.\n"
            "2. transform_load_tool: Inspecting, filtering, and transforming datasets via Pandas.\n"
            "3. execute_code_tool: Running custom Python scripts for data manipulations.\n\n"
            "Determine the necessary ETL operations based on the user's request. "
            "Call the appropriate tool with accurate arguments. Once tools have returned their results, "
            "summarize the outcome clearly for the user and complete your turn."
        )
    )
    all_messages = [system_message] + list(state.messages)
    response = llm_with_tools.invoke(all_messages)
    return {"messages": [response]}


def tool_node(state: ETLAgentSchema) -> dict:
    """Executes the tool calls produced by the LLM."""
    last_message = state.messages[-1]
    tool_results: List[ToolMessage] = []

    for tool_call in getattr(last_message, "tool_calls", []):
        tool = tools_by_name.get(tool_call["name"])
        if tool:
            print(f"[ETL Agent] Executing tool: {tool_call['name']} with args: {tool_call['args']}")
            observation = tool.invoke(tool_call["args"])
        else:
            observation = f"Error: Tool '{tool_call['name']}' not found."
        tool_results.append(ToolMessage(content=str(observation), tool_call_id=tool_call["id"]))

    return {"messages": tool_results}


def should_continue(state: ETLAgentSchema) -> str:
    """Checks if the last message contains tool calls."""
    last_message = state.messages[-1]
    if getattr(last_message, "tool_calls", None):
        return "tool_node"
    return END


# Graph Construction
etl_analyst_graph = StateGraph(ETLAgentSchema)
etl_analyst_graph.add_node("llm_node", llm_node)
etl_analyst_graph.add_node("tool_node", tool_node)

etl_analyst_graph.add_edge(START, "llm_node")
etl_analyst_graph.add_conditional_edges(
    "llm_node",
    should_continue,
    {
        "tool_node": "tool_node",
        END: END
    }
)
etl_analyst_graph.add_edge("tool_node", "llm_node")

# Compiled module export
etl_analyst = etl_analyst_graph.compile()


if __name__ == "__main__":
    test_msg = (
        "Filter the extracted data in 'data/extract/extracted_data.csv' "
        "to only keep rows where name is 'weedle', and save to 'data/transform/weedle_only.csv'."
    )
    print(f"Testing ETL Analyst: {test_msg}")
    result = etl_analyst.invoke({"messages": [HumanMessage(content=test_msg)]})
    print("\n" + "=" * 60)
    print("ETL AGENT RESPONSE:")
    print(result["messages"][-1].content)
    print("=" * 60)