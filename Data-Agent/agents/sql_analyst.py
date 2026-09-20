from models.schema import JudgeSchema
import sys
import os
# pyrefly: ignore [missing-import]
from langchain_core.messages import HumanMessage, AIMessage
from utils.db import DatabaseUtil

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.llm_pick import pick_llm
from models.schema import AgentSchema

def curate_question(state: AgentSchema) -> AgentSchema:
    user_question = state.user_question
    llm = pick_llm("low")

    response = llm.invoke(f"Curate the following question: {user_question}").content
    state.curated_ques = response
    state.messages = state.messages + [HumanMessage(content=f"{response}")]

    print(f"Curated Question: {state.curated_ques}")
    return state


def prompt_query_context(state: AgentSchema) -> AgentSchema:
    curate_question = state.curated_ques

    conn_details = {
        "host": os.getenv('host') or os.getenv('POSTGRES_HOST', 'localhost'),
        "user": os.getenv('user') or os.getenv('POSTGRES_USER', 'postgres'),
        "password": os.getenv('password') or os.getenv('POSTGRES_PASSWORD', 'postgres'),
        "database": os.getenv('database') or os.getenv('POSTGRES_DB', 'data_agent_db'),
        "port": int(os.getenv('port') or os.getenv('POSTGRES_PORT', '5432'))
    }

    obj_db = DatabaseUtil(conn_details)
    schema_info = obj_db.schema_details("public")

    # constructing the prompt query for the agent to generate the sql query
    prompt = f"""
    You are an SQL Analyst Agent. Your task is to convert the user's question into a
     SQL query that can be executed on the given database schema. You are provided with 
     the user's original query and the schema details of the database, including
     table names, column names, data types, and sample dqata for each table so that you can understand the
     structure of the database and generate an accurate sql query.
     Unless user explicitly asks for the specific number of rows, always limit the output to 10 rows.
     Note - Just generate the sql query without any explanation or additional text because this query will be
     executed directly on the database. So the output should be sql ready to be executed without any modifications.

    User's Original Question: {curate_question}

    Database Schema Details:
    {schema_info}
    """

    state.prompt_query_text = prompt
    return state

def generate_sql(state: AgentSchema) -> AgentSchema:
    prompt = state.prompt_query_text
    llm = pick_llm("high")

    generated_sql_query = llm.invoke(prompt)
    state.generated_sql_query = generated_sql_query
    return state
    

def is_safe_sql(state: AgentSchema) -> AgentSchema:
    sql_query = state.generated_sql_query

    llm = pick_llm("medium")
    llm_judge = llm.with_structured_output(JudgeSchema)

    prompt = f""" 
    You are a SQL Judge for data security and management. Your task is to determine if the given SQL query is 
    safe to execute on the database schema. The sql query should only be used for data retrieval and should not modify 
    the database in any way. Neither the sql query nor the prompt should contain any SQL commands that can modify the 
    database, such as INSERT, UPDATE, DELETE,DROP,TRUNCATE,etc. or any other command that can change the structure 
    or content of the database.If the SQL Query is safe, respond with "Yes" otherwise respond with "No". Additionaly, 
    provide comments explaining your decision.

    Here is the SQL query to check:
    {sql_query}"""

    response = llm_judge.invoke(prompt).model_dump()

    state.is_safe = response["answer"]
    state.comments = response["comments"]
    
    return state

def canceled_sql(state: AgentSchema) -> AgentSchema:
    comments = state.comments
    state.final_response = f"The generated SQL Query wad deemed unsafe to execute.The reason provided by the judge is : {comments}"
    state.messages = state.messages + [AIMessage(content=f"{state.final_response}")]
    return state

# Execute SQL Query Node
def execute_sql(state: AgentSchema) -> AgentSchema:
    conn_details = {
        "host": os.getenv('host') or os.getenv('POSTGRES_HOST', 'localhost'),
        "user": os.getenv('user') or os.getenv('POSTGRES_USER', 'postgres'),
        "password": os.getenv('password') or os.getenv('POSTGRES_PASSWORD', 'postgres'),
        "database": os.getenv('database') or os.getenv('POSTGRES_DB', 'data_agent_db'),
        "port": int(os.getenv('port') or os.getenv('POSTGRES_PORT', '5432'))
    }

    sql_query = state.generated_sql_query
    obj_db = DatabaseUtil(conn_details)
    state.sql_query_execution_result = obj_db.execute_query(sql_query)
    return state

def represent_final_answer(state: AgentSchema) -> AgentSchema:
    execution_result = state.sql_query_execution_result
    curate_question = state.curated_ques

    llm = pick_llm("low")

    prompt = f"""
    You are an SQL Analyst Agent. Your Task is to provide a final answer to the user based
    on the execution result of the sql query and the user's original question.The final answer
    should be concise, clear, and directly address the user's query. Avoid including any sql codeor technical details
    in the final answer. The Final Answer should be in a user-friendly format that is easy to understand.
    If the execution result is empty or does not provide a clear answer to the user's question, 
    explain this in a user-friendly manner.

    User's Original Question: {curate_question}
    SQL Query Execution Result: {execution_result}
    """

    final_answer = llm.invoke(prompt).content
    state.final_response = final_answer
    state.messages = state.messages + [AIMessage(content=f"{final_answer}")]
    return state