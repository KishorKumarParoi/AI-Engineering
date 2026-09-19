from utils.llm_pick import pick_llm

llm_obj = pick_llm("low")
print(llm_obj.invoke("What is the capital of France?"))

