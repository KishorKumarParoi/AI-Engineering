"""Ramp-up load test: find the maximum concurrent requests before failure."""
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
import urllib.request
import json

API_URL = "http://ae18980d895d74b308f007e777bc185a-1762723266.us-east-1.elb.amazonaws.com/api/v1/ask-agentic"
HEADERS = {"Content-Type": "application/json"}
PAYLOAD = json.dumps({
    "query": "What is attention mechanism in deep learning?",
    "top_k": 5,
    "search_mode": "hybrid"
}).encode()

TIMEOUT = 60.0


def single_request(idx: int):
    """Send one request and return (status_code, duration_ms, error)."""
    start = time.time()
    try:
        req = urllib.request.Request(API_URL, data=PAYLOAD, headers=HEADERS, method="POST")
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            body = resp.read().decode()
            duration = (time.time() - start) * 1000
            return resp.status, duration, None
    except urllib.error.HTTPError as e:
        duration = (time.time() - start) * 1000
        return e.code, duration, str(e.reason)
    except Exception as e:
        duration = (time.time() - start) * 1000
        return 0, duration, str(e)


def run_level(concurrency: int, total: int = 30):
    """Run a single concurrency level and print results."""
    print(f"\n{'=' * 60}")
    print(f"CONCURRENCY = {concurrency}  |  TOTAL REQUESTS = {total}")
    print(f"{'=' * 60}")

    results = []
    start = time.time()

    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = [executor.submit(single_request, i) for i in range(total)]
        for f in futures:
            results.append(f.result())

    total_time = time.time() - start

    # Stats
    ok = [r for r in results if r[0] == 200]
    errors = [r for r in results if r[0] != 200]
    durations = [r[1] for r in results]

    success_rate = len(ok) / total * 100
    avg_ms = sum(durations) / len(durations)
    max_ms = max(durations)

    print(f"  Success:    {len(ok)}/{total}  ({success_rate:.0f}%)")
    print(f"  Errors:     {len(errors)}")
    print(f"  Total time: {total_time:.1f}s")
    print(f"  Avg:        {avg_ms / 1000:.1f}s")
    print(f"  Max:        {max_ms / 1000:.1f}s")

    if errors:
        codes = {}
        for r in errors:
            code = r[0] if r[0] else "ERR"
            codes[code] = codes.get(code, 0) + 1
        print(f"  Error codes: {codes}")

    return success_rate


def main():
    levels = [10, 15, 20, 25, 30, 40, 50]
    for c in levels:
        sr = run_level(c, total=30)
        if sr < 50:
            print(f"\n>>> STOPPING: Success rate dropped below 50% at concurrency={c}")
            break
        # Brief pause between levels
        time.sleep(5)


if __name__ == "__main__":
    main()
