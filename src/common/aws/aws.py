import boto3
import io
import mimetypes
import os
import re
import tempfile
import uuid

from typing import Optional
from urllib.parse import urlparse

from botocore.exceptions import ClientError

from src import config
from src.common.logger.logger import get_logger


logger = get_logger(__name__)


class AWS(object):
    __shared_state = {}
    __aws_inited = False

    def __init__(self):
        self.__dict__ = self.__shared_state
        if self.__aws_inited is False:
            self.__aws_inited = True
            logger.info("Loading AWS session as __session is None")
            self.__session = self.__get_session()
            logger.info("Loading AWS session done")

    def __get_key_secret_region(self, region=None):
        key = config.AWS_ACCESS_KEY_ID
        secret = config.AWS_SECRET_ACCESS_KEY
        if region is None:
            region = config.AWS_REGION

        if not key or not secret:
            logger.error("AWS_ACCESS_KEY_ID or AWS_SECRET_ACCESS_KEY not found in environment")
            raise RuntimeError("AWS_ACCESS_KEY_ID or AWS_SECRET_ACCESS_KEY not found in environment")
        return key, secret, region

    def __get_r2_endpoint_key_secret_region(self, region=None):
        key = config.R2_ACCESS_KEY_ID
        secret = config.R2_SECRET_ACCESS_KEY
        endpoint = config.R2_ENDPOINT_URL
        region = region or config.R2_REGION
        if not key or not secret or not endpoint:
            logger.error("R2_ACCESS_KEY_ID or R2_SECRET_ACCESS_KEY or R2_ENDPOINT_URL not found in environment")
            raise RuntimeError("R2_ACCESS_KEY_ID or R2_SECRET_ACCESS_KEY or R2_ENDPOINT_URL not found in environment")
        return endpoint, key, secret, region

    @staticmethod
    def __get_session():
        session = boto3.Session()
        return session

    def get_s3_client(self, region=None):
        if self.__session is None:
            self.__session = self.__get_session()
        if (
            config.R2_ENABLED is True
            and config.R2_ENDPOINT_URL is not None
            and config.R2_ACCESS_KEY_ID is not None
            and config.R2_SECRET_ACCESS_KEY is not None
        ):
            endpoint, key, secret, region = self.__get_r2_endpoint_key_secret_region(region=region)
            return self.__session.client(
                "s3", endpoint_url=endpoint, aws_access_key_id=key, aws_secret_access_key=secret, region_name=region
            )
        key, secret, region = self.__get_key_secret_region(region=region)
        return self.__session.client("s3", aws_access_key_id=key, aws_secret_access_key=secret, region_name=region)


def get_client():
    return AWS().get_client()


def delete_file(filename):
    try:
        os.remove(filename)
    except OSError:
        logger.debug(f"file {filename} does not exist. Cannot delete.")


def get_temporary_filename(suffix=""):
    fd, out_filename = tempfile.mkstemp(suffix=suffix)
    os.close(fd)
    delete_file(out_filename)
    return out_filename


def s3_key_exists(s3, bucket_name, key):
    try:
        s3.head_object(Bucket=bucket_name, Key=key)
    except ClientError as e:
        logger.debug(e, exc_info=True)
        return False
    except Exception as e:  # pylint: disable=broad-except
        logger.debug(e, exc_info=True)
        return False
    return True


def s3_public_url(bucket: str, key: str) -> str:
    # if config.R2_ENABLED is True:
    #     cloudfront_url = R2Mapping[bucket]
    #     return f"https://{cloudfront_url}/{key}"
    # else:
    # return f"https://{bucket}.s3.amazonaws.com/{key}"
    return f"https://{bucket}.s3.amazonaws.com/{key}"


def download_from_s3(s3, bucket, key, filename=None):
    logger.debug("download_from_s3")
    if not s3_key_exists(s3, bucket, key):
        raise RuntimeError(f"Bucket: {bucket} does not contain specified key: {key}")
    suffix = key.split(".")[-1]
    if filename is None:
        if len(key.split(".")) == 1:
            filename = get_temporary_filename("")
        else:
            filename = get_temporary_filename(suffix="." + suffix)
    s3.download_file(bucket, key, filename)
    logger.debug("Downloaded to: {0}".format(filename))
    return filename


def upload_to_s3(s3, filename, bucket, key=None, public=False):
    if not os.path.exists(filename):
        raise FileNotFoundError(filename)
    content_type = mimetypes.MimeTypes().guess_type(filename)[0]
    if key is None:
        key = str(uuid.uuid4()) + os.path.splitext(filename)[1]
    extra_args = {}
    if content_type is not None:
        extra_args["ContentType"] = content_type
    if public is True:
        extra_args["ACL"] = "public-read"
    s3.upload_file(filename, bucket, key, ExtraArgs=extra_args)
    logger.debug("Uploaded %s to %s with key: %s", filename, bucket, key)
    return key


def update_to_s3(s3, bucket, key, content):
    if isinstance(content, str):
        # Convert string content to bytes
        content_bytes = content.encode("utf-8")
    elif isinstance(content, bytes):
        content_bytes = content
    elif isinstance(content, (io.BufferedIOBase, io.RawIOBase)):
        # If content is a file-like object, read its content
        content_bytes = content.read()
    else:
        raise ValueError("Unsupported content type. Expected str, bytes, or file-like object.")

    s3.put_object(ACL="public-read", Bucket=bucket, Key=key, Body=content_bytes)
    logger.debug("Updated the content to %s with key: %s", bucket, key)


def get_url_s3_data(url: str) -> Optional[dict]:
    try:
        parsed_data = urlparse(url)
        domain = parsed_data.netloc

    except Exception:
        logger.debug(f"Failed parsing s3/r2 url: {url}")
        return None

    # If URL is an .r2.cloudflarestorage.com/ type URL (Example:
    # https://pencil-production-bucket.7a35ab900ac3aac1b0bca7ab24217138.r2.cloudflarestorage.com/499/f4eb23e2-1547-40aa-b2c6-bed1566a4051.png
    if ".r2.cloudflarestorage.com" in domain:
        try:
            r2_pattern = re.compile(r"https://(?P<bucket>[^.]+)\.[^.]+\.r2\.cloudflarestorage\.com/(?P<key>[^?]+)")
            r2_match = r2_pattern.match(url.split("?")[0])

            if r2_match:
                return {"key": r2_match.group("key"), "bucket": r2_match.group("bucket"), "region": "auto"}

            else:
                return None

        except Exception as e:
            logger.debug(f"Failed parsing specific R2 url: {url}, E:{e}")
            return None

    # if "trypncl" in domain:
    #     try:
    #         key = parsed_data.path.lstrip("/")
    #         bucket = R2ReverseMapping.get(domain, "pencil-production-bucket")

    #         return {"key": key, "bucket": bucket, "region": "auto"}

    #     except Exception as e:
    #         logger.debug(f"Failed parsing r2 url: {url}, E:{e}")

    #         return None

    else:
        try:
            pattern = re.compile(r"https://(?P<s3_bucket>.*).s3.(?P<region>.*).*amazonaws.com/(?P<s3_key>.*)")
            match = pattern.match(url.split("?")[0])
            region = ""

            if match.group("region"):
                region = match.group("region") if match.group("region")[-1] != "." else match.group("region")[:-1]

            return {"key": match.group("s3_key"), "bucket": match.group("s3_bucket"), "region": region}

        except Exception as e:
            logger.debug(f"Failed parsing s3 url: {url}, E:{e}")

            return None
