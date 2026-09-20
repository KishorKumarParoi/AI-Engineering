import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.llm_pick import pick_llm
from models.schema import AgentSchema

def curate_question(state: AgentSchema) -> AgentSchema:
    user_question = state.user_question
    llm = pick_llm("low")

    response = llm.invoke(f"Curate the following question: {user_question}")
    state.curated_ques = response

    print(f"Curated Question: {state.curated_ques}")
    return state

llm_obj = pick_llm("high")
print(llm_obj.invoke("What is the capital of France?"))

