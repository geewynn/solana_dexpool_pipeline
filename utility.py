import boto3
import json
import os
from datetime import datetime

from dotenv import load_dotenv

load_dotenv()


STORAGE_ACCESS_KEY = os.getenv("STORAGE_ACCESS_KEY")
STORAGE_SECRET_KEY = os.getenv("STORAGE_SECRET_KEY")
STORAGE_ENDPOINT_URL = os.getenv("STORAGE_ENDPOINT_URL")
STORAGE_BUCKET_NAME = os.getenv("STORAGE_BUCKET_NAME")

S3 = boto3.client(
        "s3",
        aws_access_key_id=STORAGE_ACCESS_KEY,
        aws_secret_access_key=STORAGE_SECRET_KEY,
    )

def upload_to_s3(bucket: str, key: str, data: dict, log: bool = True) -> None:
    """
    Uploads a dictionary as a JSON file to an S3 bucket.

    Args:
        bucket (str): S3 bucket name
        key (str): S3 object key (path in the bucket)
        data (dict): Python dictionary to upload
        log (bool): Whether to print success log
    """
    try:
        S3.put_object(
            Bucket=bucket,
            Key=key,
            Body=json.dumps(data, indent=2),
            ContentType="application/json"
        )
        if log:
            print(f"Uploaded to s3://{bucket}/{key}")
    except Exception as e:
        print(f"Failed to upload to S3: {e}")


def get_timestamp(fmt: str = "%Y-%m-%d_%H-%M-%S") -> str:
    """Returns the current timestamp string formatted for filenames or logs."""
    return datetime.now().strftime(fmt)

def get_s3_bucket() -> str:
    """
    Returns the S3 bucket from environment variable `S3_BUCKET`.
    Raises an error if not set.
    """
    bucket = os.getenv("STORAGE_BUCKET_NAME")
    if not bucket:
        raise EnvironmentError("S3_BUCKET environment variable not set.")
    return bucket
