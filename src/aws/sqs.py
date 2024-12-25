from os import environ

import boto3

AWS_PROFILE=environ.get("AWS_PROFILE")

if AWS_PROFILE:
    boto3.setup_default_session(profile_name=AWS_PROFILE, region_name="us-east-1")

sqs_client = boto3.client(
    "sqs",
    region_name="us-east-1",
    aws_access_key_id=environ.get("AWS_ACCESS_KEY"),
    aws_secret_access_key=environ.get("AWS_SECRET_ACCESS_KEY"),
)
