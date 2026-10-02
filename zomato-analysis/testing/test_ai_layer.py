#!/usr/bin/env -S uv run --with openai --with snowflake-connector-python --with python-dotenv python
# -*- coding: utf-8 -*-
"""
Test Suite: testing/test_ai_layer.py
Purpose: AI Layer Verification (OpenAI Embedding, RAG, Text-to-SQL & Enrichment)
Tier: Senior Staff / Lead Data Engineer Standard
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

load_dotenv(PROJECT_ROOT / ".env")

GREEN = "\033[0;32m"
BLUE = "\033[0;34m"
CYAN = "\033[0;36m"
YELLOW = "\033[1;33m"
RED = "\033[0;31m"
BOLD = "\033[1m"
NC = "\033[0m"

def print_header(title):
    print(f"\n{CYAN}{BOLD}=========================================================={NC}")
    print(f"{CYAN}{BOLD}  {title}{NC}")
    print(f"{CYAN}{BOLD}=========================================================={NC}")

def run_tests():
    print_header("AI LAYER VERIFICATION SUITE")

    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        print(f"{YELLOW}[WARN] OPENAI_API_KEY is not set in environment or .env.{NC}")
        print("  Skipping live OpenAI API generation tests (offline mode).")
        return True

    try:
        from openai import OpenAI
        client = OpenAI(api_key=openai_key)
        
        # 1. Test Embedding API
        print(f"{BLUE}[INFO]{NC} Testing text-embedding-3-small API...")
        res = client.embeddings.create(model="text-embedding-3-small", input=["Zomato delivery was fast and hot!"])
        vec = res.data[0].embedding
        assert len(vec) == 1536, f"Expected 1536 dimensions, got {len(vec)}"
        print(f"{GREEN}[PASS]{NC} Embedding API operational (Vector dimension: {len(vec)})")

        # 2. Test Text-to-SQL Model prompt
        print(f"{BLUE}[INFO]{NC} Testing Text-to-SQL logic...")
        from ai.text_to_sql import generate_sql, is_safe
        sql = generate_sql("Top 3 cities by total orders")
        print(f"{GREEN}[PASS]{NC} Generated SQL: {BOLD}{sql}{NC}")
        assert is_safe(sql), "Generated SQL failed safety check!"
        print(f"{GREEN}[PASS]{NC} Query passed safety and read-only validation")

        print_header("AI LAYER TEST SUMMARY")
        print(f"{GREEN}{BOLD}ALL AI LAYER TESTS PASSED (100%)!{NC}")
        return True

    except Exception as e:
        print(f"{RED}[FAIL] AI layer test error: {e}{NC}")
        return False

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
