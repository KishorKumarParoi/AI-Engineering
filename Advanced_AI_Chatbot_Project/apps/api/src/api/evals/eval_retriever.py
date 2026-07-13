import os 
import asyncio
import openai
from qdrant_client import QdrantClient
from langchain_openai import ChatOpenAI
from langchain_openai import OpenAIEmbeddings

from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper
from dotenv import load_dotenv

from langsmith import Client, traceable, get_current_run_tree
import openai
from qdrant_client import QdrantClient

from ragas.dataset_schema import SingleTurnSample
from ragas.metrics import IDBasedContextPrecision, IDBasedContextRecall, Faithfulness, ResponseRelevancy

from api.agents.retrieval_generation import rag_pipeline

# Allow nested event loops for LangSmith's thread pool executor
import nest_asyncio
nest_asyncio.apply()

ls_client = Client()
qdrant_client = QdrantClient(url="http://localhost:6333", api_key="")  

ragas_llm = LangchainLLMWrapper(ChatOpenAI(model="gpt-4o-mini"))
ragas_embeddings = LangchainEmbeddingsWrapper(OpenAIEmbeddings(model="text-embedding-3-small"))

def ragas_faithfulness(run, example):
    """Sync wrapper for async faithfulness evaluator."""
    output = run.outputs if hasattr(run, 'outputs') else run
    sample = SingleTurnSample(
        user_input=output["question"],
        response=output["answer"],
        retrieved_contexts=output["retrieved_context"]["retrieve_context"],
    )
    scorer = Faithfulness(llm=ragas_llm)
    return asyncio.run(scorer.single_turn_ascore(sample))

def ragas_response_relevancy(run, example):
    """Sync wrapper for async response relevancy evaluator."""
    output = run.outputs if hasattr(run, 'outputs') else run
    sample = SingleTurnSample(
        user_input=output["question"],
        response=output["answer"],
        retrieved_contexts=output["retrieved_context"]["retrieve_context"],
    )
    scorer = ResponseRelevancy(llm=ragas_llm, embeddings=ragas_embeddings)
    return asyncio.run(scorer.single_turn_ascore(sample))

def ragas_context_precision_id_based(run, example):
    """Sync wrapper for async context precision evaluator."""
    output = run.outputs if hasattr(run, 'outputs') else run
    example_outputs = example.outputs if hasattr(example, 'outputs') else example
    
    # Handle both dict and object attribute access
    if isinstance(example_outputs, dict):
        ref_ids = example_outputs.get("retrieved_context_ids", [])
    else:
        ref_ids = getattr(example_outputs, "retrieved_context_ids", [])
    
    sample = SingleTurnSample(
        retrieved_context_ids=output["retrieved_context"]["retrieved_context_ids"],
        reference_context_ids=ref_ids
    )
    scorer = IDBasedContextPrecision()
    return asyncio.run(scorer.single_turn_ascore(sample))

results = ls_client.evaluate(
        lambda x: rag_pipeline(x["question"], qdrant_client, top_k=5),
        data="rag-evaluation-dataset",
        evaluators=[
            ragas_faithfulness,
            ragas_response_relevancy,
            ragas_context_precision_id_based,
        ],
        experiment_prefix="retriever",
        max_concurrency=10,
)
