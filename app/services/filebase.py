import os
from pathlib import Path

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from dotenv import load_dotenv

from logger.logger import get_logger

load_dotenv()

logger = get_logger(__name__)


class FilebaseStorage:

    def __init__(
        self,
        bucket_name: str = None,
        access_key: str = None,
        secret_key: str = None,
        endpoint_url: str = None,
        region_name: str = "us-east-1",
    ):
        self.bucket_name = (
            bucket_name or os.environ["FILEBASE_BUCKET_NAME"]
        )

        self.client = boto3.client(
            "s3",
            endpoint_url=(
                endpoint_url
                or os.environ["FILEBASE_ENDPOINT"]
            ),
            region_name=region_name,
            aws_access_key_id=(
                access_key
                or os.environ["FILEBASE_ACCESS_TOKEN"]
            ),
            aws_secret_access_key=(
                secret_key
                or os.environ["FILEBASE_SECRET_ACCESS_KEY"]
            ),
            config=Config(signature_version="s3v4"),
        )

    def initialize(self):
        try:
            self.client.head_bucket(
                Bucket=self.bucket_name
            )

            logger.info(
                f"Connected to bucket '{self.bucket_name}'"
            )

            return True

        except ClientError:
            logger.exception(
                "Failed to initialize Filebase storage."
            )
            raise

    def upload_document(
        self,
        file_name: str,
        object_name: str = None,
    ):
        try:
            object_name = (
                object_name
                or os.path.basename(file_name)
            )

            self.client.upload_file(
                Filename=file_name,
                Bucket=self.bucket_name,
                Key=str(object_name),
            )

            logger.info(
                f"Uploaded '{object_name}' successfully."
            )

            return object_name

        except ClientError:
            logger.exception(
                f"Failed to upload '{file_name}'."
            )
            raise

    def download_document(
        self,
        object_name: str,
        destination: str,
    ):
        try:
            destination = Path(destination)
            destination.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            self.client.download_file(
                Bucket=self.bucket_name,
                Key=object_name,
                Filename=str(destination),
            )

            logger.info(
                f"Downloaded '{object_name}' "
                f"to '{destination}'"
            )

            return str(destination)

        except ClientError:
            logger.exception("Download failed.")
            raise

    def delete_document(self, object_name: str):
        try:
            self.client.delete_object(
                Bucket=self.bucket_name,
                Key=object_name,
            )

            logger.info(
                f"Deleted '{object_name}' successfully."
            )

            return True

        except ClientError:
            logger.exception(
                f"Failed to delete '{object_name}'."
            )
            raise


storage = FilebaseStorage()