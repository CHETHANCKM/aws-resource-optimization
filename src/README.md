# Test infrastructure and load tests

Everything here creates **billable** AWS resources. Delete the stacks when done.

## Deploy

```bash
aws cloudformation deploy --stack-name awsro-test-ec2-dev \
  --template-file src/cf/ec2/template.yaml --capabilities CAPABILITY_IAM
aws cloudformation deploy --stack-name awsro-test-lambda-dev \
  --template-file src/cf/lambda/template.yaml --capabilities CAPABILITY_IAM
```

## Load test (local only; the scripts refuse to run in CI)

```bash
pip install boto3
python src/test/ec2_load.py --profile-tag busy --duration 600
python src/test/ec2_load.py --profile-tag steady --duration 600
python src/test/lambda_load.py --requests 500 --concurrency 20
```

Leave `awsro-test-idle-large-dev` and `awsro-test-unused-dev` untouched to get idle findings.
Wait for CloudWatch data (EC2 is hourly in the report), then generate the report.

## Clean up

```bash
aws cloudformation delete-stack --stack-name awsro-test-ec2-dev
aws cloudformation delete-stack --stack-name awsro-test-lambda-dev
```
