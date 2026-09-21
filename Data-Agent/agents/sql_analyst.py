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

    generated_sql_query = llm.invoke(prompt).content
    if "```" in generated_sql_query:
        generated_sql_query = generated_sql_query.split("```")[1]
        if generated_sql_query.startswith("sql"):
            generated_sql_query = generated_sql_query[3:]
        generated_sql_query = generated_sql_query.strip()

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

# StateGraph
sql_agent_graph = StateGraph(AgentSchema)

# Nodes
sql_agent_graph.add_node("curate_question", curate_question)
sql_agent_graph.add_node("prompt_query_context", prompt_query_context)
sql_agent_graph.add_node("generate_sql", generate_sql)
sql_agent_graph.add_node("is_safe_sql", is_safe_sql)
sql_agent_graph.add_node("canceled_sql", canceled_sql)
sql_agent_graph.add_node("execute_sql", execute_sql)
sql_agent_graph.add_node("represent_final_answer", represent_final_answer)

sql_agent_graph.add_edge(START, "curate_question")
sql_agent_graph.add_edge("curate_question", "prompt_query_context")
sql_agent_graph.add_edge("prompt_query_context", "generate_sql")
sql_agent_graph.add_edge("generate_sql", "is_safe_sql")

# Conditional Edges

def is_safe_sql_edge(state: AgentSchema) -> str: 
    is_safe = state.is_safe 
    if str(is_safe).lower() == "yes":
        return "execute_sql"
    else:
        return "canceled_sql"

sql_agent_graph.add_conditional_edges("is_safe_sql", is_safe_sql_edge,["execute_sql","canceled_sql"])
sql_agent_graph.add_edge("canceled_sql", END)
sql_agent_graph.add_edge("execute_sql", "represent_final_answer")
sql_agent_graph.add_edge("represent_final_answer", END)



if __name__ == "__main__":
    # Compile the graph
    sql_agent_workflow = sql_agent_graph.compile()

    # Visualize the graph
    try:
        from IPython.display import Image 
        img = Image(sql_agent_workflow.get_graph().draw_mermaid_png())
        with open("sql_agent_graph.png", "wb") as f:
            f.write(img.data)
        print("Graph saved to sql_agent_graph.png")
    except Exception as e:
        print(f"Could not save graph image: {e}")

    # Test the agent workflow
    input_state = {
        "user_question": "What are the different payment methods in our database?"
    }

    result = sql_agent_workflow.invoke(input_state)
    print("\n" + "=" * 50)
    print(f"User Question : {input_state['user_question']}")
    print(f"Curated Q     : {result.get('curated_ques')}")
    print(f"SQL Query     :\n{result.get('generated_sql_query')}")
    print(f"Is Safe       : {result.get('is_safe')}")
    print(f"SQL Result    : {result.get('sql_query_execution_result')}")
    print(f"Final Answer  :\n{result.get('final_response')}")
    print("=" * 50)

