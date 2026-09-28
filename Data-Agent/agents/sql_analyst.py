import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from langchain_core.messages import AIMessage, HumanMessage
from langgraph.graph import END, START, StateGraph
from models.schema import AgentSchema, JudgeSchema
from utils.db import DatabaseUtil
from utils.llm_pick import pick_llm


def curate_question(state: AgentSchema) -> dict:
    """Refines and standardizes the user's natural language question."""
    user_question = state.user_question
    llm = pick_llm("low")

    system_prompt = (
        "You are an expert Data Analyst and Prompt Engineer. Rephrase and refine the user's "
        "natural language question into a concise, unambiguous analytical query suitable for a SQL database. "
        "Do not answer the question or add conversational filler; return ONLY the refined analytical question."
    )
    response = llm.invoke([
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_question}
    ]).content.strip()

    print(f"\n[SQL Analyst] Curated Question: {response}")
    return {
        "curated_ques": response,
        "messages": [HumanMessage(content=response)]
    }


def prompt_query_context(state: AgentSchema) -> dict:
    """Inspects the database schema and prepares the context-rich SQL prompt."""
    curated_question = state.curated_ques or state.user_question
    db = DatabaseUtil()
    schema_info = db.schema_details("public")

    prompt = f"""You are an expert PostgreSQL Data Analyst. Your task is to generate a syntactically correct PostgreSQL query based on the user's question and the database schema provided.

Guidelines:
1. Generate ONLY the executable SQL query. Do not wrap in markdown or add explanations.
2. Only reference existing tables and columns shown in the schema.
3. Unless the user explicitly asks for all rows or a specific count, add LIMIT 10 to keep results concise.
4. For text comparisons, use ILIKE when appropriate.
5. Use proper joins when data spans multiple tables.

User's Question:
{curated_question}

Database Schema Details:
{schema_info}
"""
    return {"prompt_query_text": prompt}


def generate_sql(state: AgentSchema) -> dict:
    """Generates the SQL query using an advanced reasoning LLM."""
    prompt = state.prompt_query_text
    llm = pick_llm("medium")

    generated_sql = llm.invoke(prompt).content.strip()

    # Clean markdown if model wrapped it
    if "```" in generated_sql:
        parts = generated_sql.split("```")
        for part in parts:
            part_cleaned = part.strip()
            if part_cleaned.startswith("sql"):
                part_cleaned = part_cleaned[3:].strip()
            if any(kw in part_cleaned.upper() for kw in ["SELECT", "WITH"]):
                generated_sql = part_cleaned
                break

    print(f"[SQL Analyst] Generated SQL:\n{generated_sql}")
    return {"generated_sql_query": generated_sql}


def is_safe_sql(state: AgentSchema) -> dict:
    """Acts as a security judge to ensure the query is strictly read-only."""
    sql_query = state.generated_sql_query
    llm = pick_llm("low")
    llm_judge = llm.with_structured_output(JudgeSchema)

    prompt = f"""You are a SQL Security and Data Governance Judge. Verify if the provided SQL query is completely read-only and safe to execute in production.

Rules:
- Read-only queries (SELECT, WITH) that do not alter the database are SAFE -> answer='Yes'.
- Any commands that modify schema or data (INSERT, UPDATE, DELETE, DROP, TRUNCATE, ALTER, GRANT, EXEC) or dangerous operations (pg_sleep, copy) are UNSAFE -> answer='No'.

SQL Query to inspect:
{sql_query}
"""
    judge_result = llm_judge.invoke(prompt).model_dump()
    print(f"[SQL Judge] Safe: {judge_result['answer']} | Reason: {judge_result['comments']}")
    return {
        "is_safe": judge_result["answer"],
        "comments": judge_result["comments"]
    }


def canceled_sql(state: AgentSchema) -> dict:
    """Handles rejected queries safely."""
    explanation = (
        f"Security Alert: The generated SQL query was blocked by the safety judge.\n"
        f"Reason: {state.comments}\n"
        f"Query: {state.generated_sql_query}"
    )
    print(f"[SQL Analyst] {explanation}")
    return {
        "final_response": explanation,
        "messages": [AIMessage(content=explanation)]
    }


def execute_sql(state: AgentSchema) -> dict:
    """Executes the validated safe query against PostgreSQL."""
    db = DatabaseUtil()
    sql_query = state.generated_sql_query
    print(f"[SQL Analyst] Executing query on PostgreSQL...")
    result = db.execute_query(sql_query)
    return {"sql_query_execution_result": result}


def represent_final_answer(state: AgentSchema) -> dict:
    """Synthesizes execution results into a polished, stakeholder-ready response."""
    execution_result = state.sql_query_execution_result
    curated_question = state.curated_ques
    sql_query = state.generated_sql_query
    llm = pick_llm("low")

    prompt = f"""You are an executive Data Analyst presenting findings to stakeholders.
Provide a clear, well-structured, professional answer based on the SQL query execution result.

User's Question: {curated_question}
Executed SQL Query:
{sql_query}

Execution Result:
{execution_result}

Formatting Guidelines:
- State the direct answer clearly upfront.
- If data contains records, format them neatly (bullet points or a clean markdown table).
- Keep technical jargon minimal while preserving numerical accuracy.
- If no data was returned or an error occurred, explain the situation clearly.
"""
    final_answer = llm.invoke(prompt).content.strip()
    return {
        "final_response": final_answer,
        "messages": [AIMessage(content=final_answer)]
    }


# StateGraph Definition
sql_agent_graph = StateGraph(AgentSchema)

# Add Nodes
sql_agent_graph.add_node("curate_question", curate_question)
sql_agent_graph.add_node("prompt_query_context", prompt_query_context)
sql_agent_graph.add_node("generate_sql", generate_sql)
sql_agent_graph.add_node("is_safe_sql", is_safe_sql)
sql_agent_graph.add_node("canceled_sql", canceled_sql)
sql_agent_graph.add_node("execute_sql", execute_sql)
sql_agent_graph.add_node("represent_final_answer", represent_final_answer)

# Add Edges
sql_agent_graph.add_edge(START, "curate_question")
sql_agent_graph.add_edge("curate_question", "prompt_query_context")
sql_agent_graph.add_edge("prompt_query_context", "generate_sql")
sql_agent_graph.add_edge("generate_sql", "is_safe_sql")


def is_safe_sql_edge(state: AgentSchema) -> str:
    if str(state.is_safe).lower() == "yes":
        return "execute_sql"
    return "canceled_sql"


sql_agent_graph.add_conditional_edges(
    "is_safe_sql",
    is_safe_sql_edge,
    {
        "execute_sql": "execute_sql",
        "canceled_sql": "canceled_sql"
    }
)
sql_agent_graph.add_edge("canceled_sql", END)
sql_agent_graph.add_edge("execute_sql", "represent_final_answer")
sql_agent_graph.add_edge("represent_final_answer", END)

# Compile graph at module level for external import
sql_analyst = sql_agent_graph.compile()


if __name__ == "__main__":
    # Test execution
    test_question = "What are the top 5 cities with the highest number of registered users?"
    print(f"Testing SQL Analyst with question: '{test_question}'")
    result = sql_analyst.invoke({"user_question": test_question})
    print("\n" + "=" * 60)
    print("FINAL RESPONSE:")
    print(result.get("final_response"))
    print("=" * 60)
