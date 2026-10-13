# Test infrastructure and load tests

Everything here creates **billable** AWS resources. Delete the stacks when done.

## Configure

Add or edit entries in the config files, then render the templates (the deploy workflow does this too):

- `src/cf/ec2/instances.json`: `name`, `instance_type`, `profile` (`idle`/`busy`/`steady`), `volume_gb`, optional `ami`, `volume_type`.
- `src/cf/lambda/functions.json`: `name`, `memory`, `timeout`, `behavior` (`noop`/`cpu`/`flaky`), `payload`, `invoke` (false = never invoked), optional `runtime`.
- `name_suffix` (default `-dev`) is appended to every name.

```bash
python src/cf/generate.py all
```

`template.json` files are generated; edit the config, not the templates.

## Deploy

```bash
aws cloudformation deploy --stack-name awsro-test-ec2-dev \
  --template-file src/cf/ec2/template.json --capabilities CAPABILITY_IAM
aws cloudformation deploy --stack-name awsro-test-lambda-dev \
  --template-file src/cf/lambda/template.json --capabilities CAPABILITY_IAM
```

## Load test (local only; the scripts refuse to run in CI)

```bash
pip install boto3
python src/test/ec2_load.py --profile-tag busy --duration 600
python src/test/ec2_load.py --profile-tag steady --duration 600
python src/test/lambda_load.py --requests 500 --concurrency 20
```

Instances with profile `idle` and functions with `invoke: false` are left alone to get idle findings.
Wait for CloudWatch data (EC2 is hourly in the report), then generate the report.

## Clean up

```bash
aws cloudformation delete-stack --stack-name awsro-test-ec2-dev
aws cloudformation delete-stack --stack-name awsro-test-lambda-dev
```
