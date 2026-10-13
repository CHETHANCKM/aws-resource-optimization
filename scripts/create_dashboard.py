# Creates/updates the CloudWatch dashboard "awsro-dashboard" for the awsro-test EC2 and Lambda stacks.
# Resources are discovered from the CloudFormation stacks and Lambda name prefix, so re-run after redeploys.
#   python3 scripts/create_dashboard.py
#   python3 scripts/create_dashboard.py --region us-east-1 --profile myprofile --dry-run
import argparse
import json
import subprocess
import sys


def aws(args, a):
    cmd = ["aws", *args, "--region", a.region]
    if a.profile:
        cmd += ["--profile", a.profile]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        sys.exit(f"aws {' '.join(args[:2])} failed: {res.stderr.strip()}")
    return res.stdout


def instances(a):
    out = aws(["cloudformation", "describe-stacks", "--stack-name", a.ec2_stack, "--query",
               "Stacks[0].Outputs[?ends_with(OutputKey,`Id`)].[OutputKey,OutputValue]",
               "--output", "json"], a)
    return json.loads(out)


def functions(a):
    out = aws(["lambda", "list-functions", "--query",
               f"Functions[?starts_with(FunctionName,`{a.lambda_prefix}`)].FunctionName",
               "--output", "json"], a)
    return sorted(json.loads(out))


def widget(title, metrics, x, y, region, stat="Average", w=12, h=6):
    return {"type": "metric", "x": x, "y": y, "width": w, "height": h,
            "properties": {"title": title, "region": region, "stat": stat, "period": 300,
                           "view": "timeSeries", "metrics": metrics}}


def build(a):
    inst, funcs = instances(a), functions(a)
    r = a.region
    ec2 = lambda metric: [["AWS/EC2", metric, "InstanceId", i, {"label": k.replace("AwsroTest", "").replace("Id", "")}]
                          for k, i in inst]
    lam = lambda metric: [["AWS/Lambda", metric, "FunctionName", f] for f in funcs]
    widgets = [
        {"type": "text", "x": 0, "y": 0, "width": 24, "height": 1,
         "properties": {"markdown": "# awsro test resources: EC2 and Lambda"}},
        widget("EC2 CPUUtilization (%)", ec2("CPUUtilization"), 0, 1, r),
        widget("EC2 CPUCreditBalance", ec2("CPUCreditBalance"), 12, 1, r),
        widget("EC2 NetworkIn (bytes)", ec2("NetworkIn"), 0, 7, r, "Sum"),
        widget("EC2 NetworkOut (bytes)", ec2("NetworkOut"), 12, 7, r, "Sum"),
        widget("EC2 StatusCheckFailed", ec2("StatusCheckFailed"), 0, 13, r, "Maximum"),
        widget("Lambda Invocations", lam("Invocations"), 12, 13, r, "Sum"),
        widget("Lambda Errors", lam("Errors"), 0, 19, r, "Sum"),
        widget("Lambda Duration (avg ms)", lam("Duration"), 12, 19, r),
        widget("Lambda Throttles", lam("Throttles"), 0, 25, r, "Sum"),
        widget("Lambda ConcurrentExecutions (max)", lam("ConcurrentExecutions"), 12, 25, r, "Maximum"),
    ]
    return {"widgets": widgets}


def main():
    p = argparse.ArgumentParser(description="Create the awsro-dashboard CloudWatch dashboard.")
    p.add_argument("--region", default="us-east-1")
    p.add_argument("--profile")
    p.add_argument("--name", default="awsro-dashboard")
    p.add_argument("--ec2-stack", default="awsro-test-ec2-dev")
    p.add_argument("--lambda-prefix", default="awsro-test-")
    p.add_argument("--dry-run", action="store_true", help="print the dashboard JSON only")
    a = p.parse_args()
    body = json.dumps(build(a))
    if a.dry_run:
        print(json.dumps(json.loads(body), indent=2))
        return
    aws(["cloudwatch", "put-dashboard", "--dashboard-name", a.name, "--dashboard-body", body], a)
    print(f"dashboard '{a.name}' created: "
          f"https://{a.region}.console.aws.amazon.com/cloudwatch/home?region={a.region}#dashboards:name={a.name}")


if __name__ == "__main__":
    main()
