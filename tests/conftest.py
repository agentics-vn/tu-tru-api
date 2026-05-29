"""Register custom pytest markers."""

import os

# High limit so integration suite does not hit in-process rate limiter (P3-04).
os.environ.setdefault("RATE_LIMIT_PER_MINUTE", "100000")


def pytest_configure(config):
    config.addinivalue_line("markers", "direction_c: Direction C contract tests")
