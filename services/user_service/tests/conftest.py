import os
import sys
import pytest
import boto3
from moto import mock_aws

# เพิ่ม project root ใน sys.path
PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)


@pytest.fixture(scope="function")
def aws_credentials():
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "ap-southeast-1"


@pytest.fixture(scope="function")
def mock_dynamodb_table(aws_credentials):
    """สร้าง Table จำลอง (Mock) ใน Moto"""
    os.environ["DYNAMO_TABLE_NAME"] = "TestUsers"
    with mock_aws():
        dynamodb = boto3.resource("dynamodb")
        dynamodb.create_table(
            TableName="TestUsers",
            KeySchema=[{"AttributeName": "UserID", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "UserID", "AttributeType": "S"}],
            ProvisionedThroughput={"ReadCapacityUnits": 5, "WriteCapacityUnits": 5},
        )
        yield dynamodb.Table("TestUsers")
