#!/usr/bin/env python3
"""Test script to fetch productivity tips and quotes from Tavily."""

import os
from datetime import date
from tavily import TavilyClient
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("TAVILY_API_KEY")
if not api_key:
    print("Error: TAVILY_API_KEY not found in .env")
    exit(1)

client = TavilyClient(api_key=api_key)
today = date.today().isoformat()

print("=" * 60)
print("Testing Tavily Integration")
print("=" * 60)

# Test 1: Productivity tip for developers
print(f"\n1. Searching for: 'productivity tip for developers {today}'")
try:
    response = client.search(
        query=f"productivity tip for developers {today}",
        max_results=2
    )
    print(f"   Results found: {len(response.get('results', []))}")
    for i, result in enumerate(response.get("results", []), 1):
        print(f"\n   Result {i}:")
        print(f"   Title: {result.get('title', 'N/A')[:80]}")
        print(f"   Content: {result.get('content', 'N/A')[:150]}")
        print(f"   Source: {result.get('source', 'N/A')}")
except Exception as e:
    print(f"   Error: {e}")

# Test 2: Motivational quote
print(f"\n2. Searching for: 'motivational quote for work today'")
try:
    response = client.search(
        query="motivational quote for work today",
        max_results=2
    )
    print(f"   Results found: {len(response.get('results', []))}")
    for i, result in enumerate(response.get("results", []), 1):
        print(f"\n   Result {i}:")
        print(f"   Title: {result.get('title', 'N/A')[:80]}")
        print(f"   Content: {result.get('content', 'N/A')[:150]}")
        print(f"   Source: {result.get('source', 'N/A')}")
except Exception as e:
    print(f"   Error: {e}")

# Test 3: Developer news
print(f"\n3. Searching for: 'latest developer productivity news'")
try:
    response = client.search(
        query="latest developer productivity news",
        max_results=2
    )
    print(f"   Results found: {len(response.get('results', []))}")
    for i, result in enumerate(response.get("results", []), 1):
        print(f"\n   Result {i}:")
        print(f"   Title: {result.get('title', 'N/A')[:80]}")
        print(f"   Content: {result.get('content', 'N/A')[:150]}")
        print(f"   Source: {result.get('source', 'N/A')}")
except Exception as e:
    print(f"   Error: {e}")

print("\n" + "=" * 60)
print("Test complete!")
print("=" * 60)
