"""Generate CPU load on awsro-test EC2 instances through SSM (no SSH needed).

Targets instances tagged Purpose=awsro-test and Profile=<busy|steady>.
Requires the SSM agent to be online (the CloudFormation template sets this up).
"""
from __future__ import annotations

import argparse
import os
import time

import boto3

# CPU workers as a percentage of cores; "steady" keeps utilization moderate.
PROFILES = {"busy": 100, "steady": 40}


def find_instances(ec2, profile: str) -> list[str]:
    pages = ec2.get_paginator("describe_instances").paginate(
        Filters=[
            {"Name": "tag:Purpose", "Values": ["awsro-test"]},
            {"Name": "tag:Profile", "Values": [profile]},
            {"Name": "instance-state-name", "Values": ["running"]},
        ]
    )
    return [i["InstanceId"] for p in pages for r in p["Reservations"] for i in r["Instances"]]


def main() -> None:
    if os.environ.get("CI") or os.environ.get("GITHUB_ACTIONS"):
        raise SystemExit("Load tests can only be run locally, not in CI.")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile-tag", choices=sorted(PROFILES), default="busy")
    parser.add_argument("--duration", type=int, default=600, help="seconds of load")
    parser.add_argument("--region", default=None)
    parser.add_argument("--aws-profile", default=None)
    args = parser.parse_args()

    session = boto3.Session(profile_name=args.aws_profile, region_name=args.region)
    ids = find_instances(session.client("ec2"), args.profile_tag)
    if not ids:
        raise SystemExit("No running awsro-test instances found for that profile.")

    load = PROFILES[args.profile_tag]
    commands = [
        "dnf install -y stress-ng >/dev/null 2>&1 || yum install -y stress-ng >/dev/null 2>&1",
        f"stress-ng --cpu 0 --cpu-load {load} --timeout {args.duration}s",
    ]
    ssm = session.client("ssm")
    resp = ssm.send_command(
        InstanceIds=ids,
        DocumentName="AWS-RunShellScript",
        Parameters={"commands": commands, "executionTimeout": [str(args.duration + 300)]},
        TimeoutSeconds=args.duration + 300,
    )
    command_id = resp["Command"]["CommandId"]
    print(f"Started {args.profile_tag} load ({load}% CPU, {args.duration}s) on {ids}")
    print(f"SSM command id: {command_id}")

    for instance_id in ids:
        while True:
            try:
                inv = ssm.get_command_invocation(CommandId=command_id, InstanceId=instance_id)
            except ssm.exceptions.InvocationDoesNotExist:
                time.sleep(3)
                continue
            if inv["Status"] not in ("Pending", "InProgress", "Delayed"):
                print(f"{instance_id}: {inv['Status']}")
                break
            time.sleep(15)
    print("Note: CloudWatch EC2 metrics lag a few minutes and are hourly-aggregated by the report.")


if __name__ == "__main__":
    main()
