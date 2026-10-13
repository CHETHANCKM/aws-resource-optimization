"""Invoke awsro-test Lambda functions concurrently to generate CloudWatch metrics."""
from __future__ import annotations

import argparse
import os
import json
import time
from concurrent.futures import ThreadPoolExecutor

import boto3

# function name -> payload
TARGETS = {
    "awsro-test-overprovisioned-dev": {},
    "awsro-test-underprovisioned-dev": {"n": 5_000_000},
    "awsro-test-flaky-dev": {"fail_rate": 0.3},
}


def main() -> None:
    if os.environ.get("CI") or os.environ.get("GITHUB_ACTIONS"):
        raise SystemExit("Load tests can only be run locally, not in CI.")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--requests", type=int, default=500, help="invocations per function")
    parser.add_argument("--concurrency", type=int, default=20)
    parser.add_argument("--region", default=None)
    parser.add_argument("--aws-profile", default=None)
    args = parser.parse_args()

    session = boto3.Session(profile_name=args.aws_profile, region_name=args.region)
    client = session.client("lambda")

    def invoke(item: tuple[str, dict]) -> tuple[str, bool]:
        name, payload = item
        resp = client.invoke(FunctionName=name, Payload=json.dumps(payload).encode())
        resp["Payload"].read()
        return name, "FunctionError" not in resp

    work = [(n, p) for n, p in TARGETS.items() for _ in range(args.requests)]
    start = time.time()
    results: dict[str, list[int]] = {n: [0, 0] for n in TARGETS}
    with ThreadPoolExecutor(max_workers=args.concurrency) as pool:
        for name, ok in pool.map(invoke, work):
            results[name][0 if ok else 1] += 1

    print(f"Completed {len(work)} invocations in {time.time() - start:.1f}s")
    for name, (ok, failed) in results.items():
        print(f"  {name}: {ok} ok, {failed} failed")
    print("awsro-test-unused-dev is intentionally never invoked.")


if __name__ == "__main__":
    main()
