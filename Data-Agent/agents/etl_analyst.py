import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from models.schema import ETLAgentSchema

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
def transform_load_tool(file_path: str, output_folder: str, output_format: str, user_question: str) -> str:
    """
    Transforms the given dataframe according to the ETL requirements and saves it.

    Args:
        file_path: The path to the file to transform.
        output_folder: The folder or path where the transformed dataframe will be loaded.
        output_format: The format in which to load the transformed dataframe.
        user_question: The user's transformation instruction.
    Returns:
        str: A message indicating the success or failure of the transformation.
    """
    try:
        import re

        etl_tools = ETLTools()
        top_3_rows = etl_tools.transform_load_context(file_path, output_folder, output_format)
        llm = pick_llm("low")

        # Determine exact target file path
        if output_folder.endswith(f".{output_format}"):
            target_file = output_folder
        else:
            # Check if user specified a specific file path in their query
            file_match = re.search(r"['\"]([^'\"]+\." + re.escape(output_format) + r")['\"]", user_question)
            if file_match and ("save" in user_question.lower() or "to" in user_question.lower()):
                target_file = file_match.group(1)
            else:
                target_file = os.path.join(output_folder, f"transformed_data.{output_format}")

        # Ensure target directory exists
        target_dir = os.path.dirname(target_file)
        if target_dir:
            os.makedirs(target_dir, exist_ok=True)

        prompt = f"""
        You are an expert data engineer. Provide ONLY runnable Python pandas code to perform the ETL transformation.
        Do not provide any explanation, text, or markdown code blocks. Output pure Python code.

        Source file: '{file_path}'
        Target destination file: '{target_file}'
        Target format: {output_format}

        User instruction:
        {user_question}

        Context of the data to transform (first rows):
        {top_3_rows}

        Rules:
        1. Read the dataset from '{file_path}'.
        2. Apply the requested filtering/transformation.
        3. Save the resulting dataframe EXACTLY to '{target_file}' (e.g. df.to_{output_format}('{target_file}', index=False)).
        Do NOT change the destination filename.
        """

        response = llm.invoke(prompt).content

        # Clean code
        pandas_code = response.strip()
        if "```" in pandas_code:
            parts = pandas_code.split("```")
            for part in parts:
                cleaned = part.strip()
                if cleaned.startswith("python"):
                    cleaned = cleaned[6:].strip()
                if "import " in cleaned or "read_" in cleaned or "pd." in cleaned:
                    pandas_code = cleaned
                    break

        print("\n--- Executing Generated Pandas Code ---")
        print(pandas_code)
        print("---------------------------------------\n")

        result = etl_tools.execute_code(pandas_code)

        # Fallback verification: ensure target_file exists
        if not os.path.exists(target_file):
            # Check if it was saved under another name in the target dir
            if target_dir and os.path.exists(target_dir):
                for f in os.listdir(target_dir):
                    if f.endswith(f".{output_format}") and f != os.path.basename(target_file):
                        alt_path = os.path.join(target_dir, f)
                        import shutil
                        shutil.copyfile(alt_path, target_file)
                        break

        if os.path.exists(target_file):
            return f"Data successfully transformed and saved to '{target_file}' (Result: {result})."
        else:
            return f"Transformation code executed ({result}), but target file '{target_file}' was not created."

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

tools = [extract_load_tool, transform_load_tool, execute_code_tool]
llm = pick_llm("high")
llm_bind = llm.bind_tools(tools)


# Agent Graph

def llm_node(state: ETLAgentSchema):
    messages = state.messages
    prompt = f"""
    You are an expert data engineer and analyst who has access to tools that can extract and load, transform and load data. You will be provided with a user's question and you would 
    need to perform the right etl operations as per the user's question. If the operation is performed then inform the user and end the conversation.
    Here's the chat history: {messages}\n
    """

    final_answer = llm_bind.invoke(prompt)
    state.messages = messages + [final_answer]
    return state

def tool_node(state:ETLAgentSchema):
    tool_results = []
    tools_by_name = {tool.name: tool for tool in tools}
    tool_calls = state.messages[-1].tool_calls

    for tool_call in tool_calls:
        tool = tools_by_name.get(tool_call["name"])
        observation = tool.invoke(tool_call["args"])
        tool_results.append(ToolMessage(content=observation, tool_call_id = tool_call['id']))
    state.messages = state.messages + tool_results
    return state

# Nodes and Edges

etl_analyst_graph = StateGraph(ETLAgentSchema)
etl_analyst_graph.add_node("llm_node", llm_node)
etl_analyst_graph.add_node("tool_node", tool_node)

etl_analyst_graph.add_edge(START, "llm_node")

def is_tool_call(state: ETLAgentSchema):
    last_message = state.messages[-1]
    if getattr(last_message, "tool_calls", None):
        return "tool_node"
    return END


etl_analyst_graph.add_conditional_edges(
    "llm_node",
    is_tool_call,
    ["tool_node", END]
)

etl_analyst_graph.add_edge("tool_node", "llm_node")

if __name__ == "__main__":
    etl_analyst = etl_analyst_graph.compile()

    # from IPython.display import display, Image 
    # img = Image(etl_analyst.get_graph().draw_mermaid_png())
    
    # with open("etlag_agent_graph.png", "wb") as f:
    #     f.write(img.data)

    response = etl_analyst.invoke({
        "messages": [HumanMessage(content=f"""I want to transform the data stored in the 'data/extract/extracted_data.csv' file and save it to 'data/transform/transformed_data.csv' file.
        The transformation should filter the data to show weedle pokemon only.
        """)]
    })
    
    print(response['messages'][-1].content)

    