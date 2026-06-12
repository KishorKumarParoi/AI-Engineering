import yaml
from jinja2 import Template
from langsmith import Client

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Retrieve API keys from environment variables
openai_api_key = os.getenv('OPENAI_API_KEY')
google_api_key = os.getenv('GEMINI_API_KEY')
qdrant_url = os.getenv('QDRANT_URL')
qdrant_api_key = os.getenv('QDRANT_API_KEY')
langsmith_api_key = os.getenv('LANGSMITH_API_KEY')
cohere_api_key = os.getenv('COHERE_API_KEY')
if qdrant_url and "qdrant:6333" in qdrant_url:
    # Docker service host is not resolvable from a local notebook kernel
    qdrant_url = qdrant_url.replace("qdrant:6333", "localhost:6333")

# Verify keys are loaded
print(f"OpenAI API Key present: {bool(openai_api_key)}")
print(f"Google API Key present: {bool(google_api_key)}")
print(f"Qdrant URL present: {bool(qdrant_url)}")
print(f"Qdrant API Key present: {bool(qdrant_api_key)}")
print(f"Langsmith API Key present: {bool(langsmith_api_key)}")
print(f"Cohere API Key present: {bool(cohere_api_key)}")


ls_client = Client()
ls_prompt = ls_client.pull_prompt("retrieval_generation_prompt")
ls_template = ls_prompt.messages[0].prompt.template

preprocessed_context = "- a \n - b"
question = "What is a?"

def build_prompt_with_jinja(preprocessed_context, question):
    jinja_template = """You are a helpful shopping assistant for answering questions about products in stock.
      You will be given a question and a list of context

      Instructions:
      - You need to answer the question based on the provided context only
      - Never use word context and refer to it as the available products
      - As an output you need to provide:

      * The answer to the question based on the provided context
      * The list of the IDs of the chuns that were used to answer the question.
      only return the ones that are used in the answer.
      * Short description (1-2 sentences) of the item based on the description provided in the context

      - The short description should have the name of the item.
      - The answer to the question should contain detailed information about the product and returned with
      detailed specification in bullet points.

      Context:
        {{preprocessed_context}}
      Question: 
        {{question}}
    """

    template = Template(jinja_template)
    rendered_template = template.render(preprocessed_context=preprocessed_context, question=question)
    return rendered_template

def prompt_template_config(yaml_file, prompt_key):
    with open(yaml_file, 'r') as file:
        config = yaml.safe_load(file)

    prompt_entry = config['prompts'][prompt_key]
    template_content = prompt_entry['template'] if isinstance(prompt_entry, dict) else prompt_entry

    template = Template(template_content)

    return template


def prompt_template_registry(prompt_name):
    template_content = ls_client.pull_prompt(prompt_name).messages[0].prompt.template
    template = Template(template_content)
    return template


print(prompt_template_registry("retrieval_generation_prompt").render(preprocessed_context=preprocessed_context, question=question))