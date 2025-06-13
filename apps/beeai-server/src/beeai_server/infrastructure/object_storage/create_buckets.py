# Copyright 2025 © BeeAI a Series of LF Projects, LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import asyncio
import logging
from datetime import timedelta

from aioboto3 import Session
from botocore.exceptions import ClientError
from tenacity import retry, stop_after_delay, wait_fixed

from beeai_server import get_configuration
from beeai_server.configuration import ObjectStorageConfiguration

logger = logging.getLogger(__name__)


def _get_client(config: ObjectStorageConfiguration):
    session = Session()
    return session.client(
        "s3",
        endpoint_url=str(config.endpoint_url),
        aws_access_key_id=config.access_key_id.get_secret_value(),
        aws_secret_access_key=config.access_key_secret.get_secret_value(),
        region_name=config.region,
        use_ssl=config.use_ssl,
    )


@retry(stop=stop_after_delay(timedelta(seconds=5)), wait=wait_fixed(2), reraise=True)
async def _wait_for_db(config: ObjectStorageConfiguration):
    logger.info("Waiting for object storage to be ready...")
    async with _get_client(config) as s3:
        try:
            await s3.head_bucket(Bucket=config.bucket_name)
        except ClientError as e:
            if e.response["Error"]["Code"] != "404":
                raise


async def create_buckets(config: ObjectStorageConfiguration, wait_for_db: bool = True):
    if wait_for_db:
        await _wait_for_db(config)
    async with _get_client(config) as s3:
        try:
            await s3.head_bucket(Bucket=config.bucket_name)
            logger.info(f"Bucket {config.bucket_name} already exists")
        except ClientError as e:
            if e.response["Error"]["Code"] != "404":
                raise
            await s3.create_bucket(Bucket=config.bucket_name)
            logger.info(f"Bucket {config.bucket_name} created")


if __name__ == "__main__":
    asyncio.run(create_buckets(get_configuration()._object_storage))
