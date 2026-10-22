import pytest
from app.gateway.resilience import retry_with_jitter


def test_retry_eventual_success():
    calls = 0

    @retry_with_jitter(max_retries=3, base_delay=0.01, max_delay=0.05)
    def flaky_func():
        nonlocal calls
        calls += 1
        if calls < 3:
            raise ConnectionError("Temporary glitch")
        return "SUCCESS"

    res = flaky_func()
    assert res == "SUCCESS"
    assert calls == 3
