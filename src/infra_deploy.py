# src/infra_deploy.py

import boto3
from botocore.exceptions import ClientError


def deploy_small_serverless_web(project_name: str, region: str = "us-east-1"):
    bucket_name = f"{project_name}-static-site".lower()
    table_name = f"{project_name}-data"

    s3 = boto3.client("s3", region_name=region)
    dynamodb = boto3.client("dynamodb", region_name=region)

    logs: list[str] = []
    logs.append(f"[INFO] region = {region}")
    logs.append(f"[INFO] S3 bucket = {bucket_name}")
    logs.append(f"[INFO] DynamoDB table = {table_name}")

    # 1) S3 버킷 생성
    logs.append("\n[STEP 1] S3 버킷 생성 시도...")
    try:
        if region == "us-east-1":
            s3.create_bucket(Bucket=bucket_name)
        else:
            s3.create_bucket(
                Bucket=bucket_name,
                CreateBucketConfiguration={"LocationConstraint": region},
            )
        logs.append(f"  ✅ S3 버킷 생성 완료: {bucket_name}")
    except ClientError as e:
        code = e.response["Error"]["Code"]
        if code in ("BucketAlreadyOwnedByYou", "BucketAlreadyExists"):
            logs.append(f"  ⚠️ 이미 존재하는 버킷: {bucket_name} ({code})")
        else:
            logs.append(f"  ❌ S3 버킷 생성 실패: {e}")

    # 2) DynamoDB 테이블 생성
    logs.append("\n[STEP 2] DynamoDB 테이블 생성 시도...")
    try:
        dynamodb.create_table(
            TableName=table_name,
            BillingMode="PAY_PER_REQUEST",
            AttributeDefinitions=[
                {"AttributeName": "id", "AttributeType": "S"},
            ],
            KeySchema=[
                {"AttributeName": "id", "KeyType": "HASH"},
            ],
        )
        logs.append(
            "  ⏳ 테이블 생성 요청 완료 (ACTIVE 될 때까지 수 초 ~ 수십 초 걸릴 수 있음)"
        )
        waiter = dynamodb.get_waiter("table_exists")
        waiter.wait(TableName=table_name)

        resp = dynamodb.describe_table(TableName=table_name)
        status = resp["Table"]["TableStatus"]  # 보통 'ACTIVE'
        logs.append(f"  ✅ DynamoDB 테이블 생성 완료 (상태: {status})")

    except ClientError as e:
        code = e.response["Error"]["Code"]
        if code == "ResourceInUseException":
            logs.append(f"  ⚠️ 이미 존재하는 테이블: {table_name}")
        else:
            logs.append(f"  ❌ DynamoDB 테이블 생성 실패: {e}")

    return {
        "project_name": project_name,
        "region": region,
        "bucket_name": bucket_name,
        "table_name": table_name,
        "logs": logs,
    }


# 앞으로 패턴별로 여기만 확장하면 됨
DEPLOYERS = {
    "small_serverless_web": deploy_small_serverless_web,
    # "classic_3tier": deploy_classic_3tier,  # 나중에 추가
    # "batch_analytics_pipeline": deploy_batch_analytics,  # 나중에 추가
}
