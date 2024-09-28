import os
from typing import List, Any
from minio import Minio
from minio.error import S3Error
import logging

from app.config import cfg

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MinioClient:

    def __init__(self):
        self.client = Minio(
            endpoint=cfg.minio_endpoint,
            access_key=cfg.minio_credentials["access_key"],
            secret_key=cfg.minio_credentials["secret_key"],
            secure=cfg.MINIO_SECURE
        )
        logger.info(f"Initialized MinioClient with endpoint: {cfg.minio_endpoint}")

    def list_files(self, bucket_name: str) -> List[str]:
        try:
            if not self.client.bucket_exists(bucket_name):
                raise ValueError(f"Bucket '{bucket_name}' does not exist.")

            objects = self.client.list_objects(bucket_name, recursive=True)
            file_list = [obj.object_name for obj in objects]
            logger.info(f"Listed {len(file_list)} files in bucket '{bucket_name}'.")
            return file_list

        except S3Error as e:
            logger.error(f"Error listing files in bucket '{bucket_name}': {e}")
            raise

    def put_file(self, bucket_name: str, object_name: str, file_content: Any) -> bool:
        try:
            if not self.client.bucket_exists(bucket_name):
                logger.info(f"Bucket '{bucket_name}' does not exist. Creating bucket.")
                self.client.make_bucket(bucket_name)

            self.client.put_object(
                    bucket_name=bucket_name,
                    object_name=object_name,
                    data=file_content,
                    length=file_content.size
                )
            logger.info(f"Uploaded '{object_name}' to bucket '{bucket_name}'.")
            return True

        except S3Error as e:
            logger.error(f"Error uploading file '{object_name}' to bucket '{bucket_name}': {e}")
            raise

    def get_file(self, bucket_name: str, object_name: str) -> Any:
        try:
            if not self.client.bucket_exists(bucket_name):
                raise ValueError(f"Bucket '{bucket_name}' does not exist.")

            try:
                self.client.stat_object(bucket_name, object_name)
            except S3Error as e:
                if e.code == "NoSuchKey":
                    raise ValueError(f"Object '{object_name}' does not exist in bucket '{bucket_name}'.")
                else:
                    raise

            data = self.client.get_object(bucket_name, object_name)
            return data

        except S3Error as e:
            logger.error(f"Error downloading file '{object_name}' from bucket '{bucket_name}': {e}")
            raise
        except ValueError as ve:
            logger.error(ve)
            raise
