import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from langchain_core.messages import HumanMessage
from utils.db import DatabaseUtil

from models.schema import JudgeSchema

from utils.llm_pick import pick_llm

llm = pick_llm("medium")
llm_judge = llm.with_structured_output(JudgeSchema)

sql_query = "DELETE FROM users WHERE age > 30"

prompt = f""" 
You are a SQL Judge for data security and management. Your task is to determine if the given SQL query is 
safe to execute on the database schema. The sql query should only be used for data retrieval and should not modify the database in any way.
Neither the sql query nor the prompt should contain any SQL commands that can modify the database, such as INSERT, UPDATE, DELETE,DROP,TRUNCATE,etc.
or any other command that can change the structure or content of the database.If the SQL Query is safe, respond with "Yes" otherwise respond
with "No". Additionaly, provide comments explaining your decision.
"""
prompt+=f"""
Here is the SQL query to check:
{sql_query}
"""
response = llm_judge.invoke(prompt).model_dump()
print(response)