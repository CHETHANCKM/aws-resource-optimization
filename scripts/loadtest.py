# Load-test helper for the awsro-test EC2 and Lambda stacks.
# Uses only the AWS CLI (no boto3). Examples:
#   python3 scripts/loadtest.py lambda --function awsro-test-flaky-dev --invocations 200 --concurrency 20
#   python3 scripts/loadtest.py lambda --all --invocations 100 --concurrency 10
#   python3 scripts/loadtest.py ec2 --instance-id i-0a33936a501e3fb58 --cpu-workers 2 --duration 600
#   python3 scripts/loadtest.py --dry-run ec2 --all --duration 300
import argparse
import json
import subprocess
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor

# Payloads match src/cf/lambda/functions.json; "unused" is skipped on purpose.
DEFAULT_PAYLOADS = {
    "awsro-test-overprovisioned": {},
    "awsro-test-underprovisioned": {"n": 5000000},
    "awsro-test-flaky": {"fail_rate": 0.3},
}


def aws(args, profile, region, check=True):
    cmd = ["aws", *args, "--region", region]
    if profile:
        cmd += ["--profile", profile]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if check and res.returncode != 0:
        sys.exit(f"aws {' '.join(args[:2])} failed: {res.stderr.strip()}")
    return res


def invoke_once(name, payload, profile, region):
    with tempfile.NamedTemporaryFile(suffix=".json") as out:
        start = time.time()
        res = aws(["lambda", "invoke", "--function-name", name,
                   "--payload", json.dumps(payload), "--cli-binary-format", "raw-in-base64-out",
                   out.name, "--query", "FunctionError", "--output", "text"],
                  profile, region, check=False)
        err = res.returncode != 0 or res.stdout.strip() not in ("", "None")
        return err, time.time() - start


def run_lambda(a):
    if a.all:
        names = [f"{k}{a.suffix}" for k in DEFAULT_PAYLOADS]
    elif a.function:
        names = [a.function]
    else:
        sys.exit("lambda: pass --function NAME or --all")
    for name in names:
        base = name[:-len(a.suffix)] if a.suffix and name.endswith(a.suffix) else name
        payload = json.loads(a.payload) if a.payload else DEFAULT_PAYLOADS.get(base, {})
        print(f"{name}: {a.invocations} invocations, concurrency {a.concurrency}, payload {payload}")
        if a.dry_run:
            continue
        with ThreadPoolExecutor(max_workers=a.concurrency) as pool:
            results = list(pool.map(lambda _: invoke_once(name, payload, a.profile, a.region),
                                    range(a.invocations)))
        errors = sum(1 for e, _ in results if e)
        durs = sorted(d for _, d in results)
        print(f"  done: errors={errors}/{len(results)} "
              f"avg={sum(durs) / len(durs):.2f}s p95={durs[max(int(len(durs) * 0.95) - 1, 0)]:.2f}s")


def stack_instances(a):
    res = aws(["cloudformation", "describe-stacks", "--stack-name", a.stack,
               "--query", "Stacks[0].Outputs[?ends_with(OutputKey,`Id`)].OutputValue",
               "--output", "json"], a.profile, a.region)
    return json.loads(res.stdout)


def run_ec2(a):
    if a.all:
        ids = stack_instances(a)
    elif a.instance_id:
        ids = a.instance_id
    else:
        sys.exit("ec2: pass --instance-id ID (repeatable) or --all")
    # stress-ng is installed on demand; the instances must have SSM access.
    cmd = (f"(command -v stress-ng >/dev/null || sudo dnf install -y stress-ng || sudo yum install -y stress-ng); "
           f"stress-ng --cpu {a.cpu_workers} --cpu-load {a.cpu_load} --timeout {a.duration}s")
    print(f"instances={ids} command={cmd}")
    if a.dry_run:
        return
    res = aws(["ssm", "send-command", "--document-name", "AWS-RunShellScript",
               "--instance-ids", *ids, "--parameters", json.dumps({"commands": [cmd]}),
               "--timeout-seconds", str(a.duration + 300),
               "--query", "Command.CommandId", "--output", "text"], a.profile, a.region)
    print(f"sent SSM command {res.stdout.strip()}; watch CPUUtilization in CloudWatch for ~{a.duration}s")


def main():
    p = argparse.ArgumentParser(description="Load test awsro-test Lambda functions and EC2 instances.")
    p.add_argument("--profile", help="AWS profile name")
    p.add_argument("--region", default="us-east-1")
    p.add_argument("--dry-run", action="store_true", help="print what would run, send nothing")
    sub = p.add_subparsers(dest="target", required=True)

    lp = sub.add_parser("lambda", help="invoke Lambda functions concurrently")
    lp.add_argument("--function", help="function name")
    lp.add_argument("--all", action="store_true", help="test overprovisioned, underprovisioned and flaky")
    lp.add_argument("--suffix", default="-dev", help="name suffix used with --all")
    lp.add_argument("--invocations", type=int, default=100)
    lp.add_argument("--concurrency", type=int, default=10)
    lp.add_argument("--payload", help="JSON payload (overrides defaults)")
    lp.set_defaults(func=run_lambda)

    ep = sub.add_parser("ec2", help="generate CPU load via SSM + stress-ng")
    ep.add_argument("--instance-id", action="append", help="repeatable")
    ep.add_argument("--all", action="store_true", help="all instances in --stack")
    ep.add_argument("--stack", default="awsro-test-ec2-dev")
    ep.add_argument("--cpu-workers", type=int, default=2)
    ep.add_argument("--cpu-load", type=int, default=80, help="target CPU %% per worker")
    ep.add_argument("--duration", type=int, default=300, help="seconds")
    ep.set_defaults(func=run_ec2)

    a = p.parse_args()
    a.func(a)


if __name__ == "__main__":
    main()
