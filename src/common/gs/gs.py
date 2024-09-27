import os
import mimetypes
import uuid

from typing import Optional, Tuple

import src.config as config

from google.cloud import storage
from retry import retry

from src.common.logger.logger import get_logger


logger = get_logger(__name__)


class GS(object):
    __shared_state = {}
    __gs_inited = False

    def __init__(self):
        self.__dict__ = self.__shared_state
        if self.__gs_inited is False:
            self.__gs_inited = True

            self.__client = storage.Client()
            logger.info("GS Initialized")

    def get_gs_client(self):
        if not self.__gs_inited:
            self.__client = storage.Client()

        return self.__client


# LL - also wrapping this with retry for 2nd-level guard
@retry(delay=1, backoff=2, max_delay=4, tries=5)
def download_from_gs(gs, bucket_name: str, key: str, filename: str):
    bucket = gs.bucket(bucket_name)
    blob = bucket.blob(key)
    blob.download_to_filename(filename)
    logger.info(f"Downloaded {key} from bucket {bucket.name} to {filename}")


# LL - also wrapping this with retry for 2nd-level guard
@retry(delay=1, backoff=2, max_delay=4, tries=5)
def upload_to_gs(
    gs, filename: str, bucket: str, key: Optional[str] = None, public: Optional[bool] = False
) -> Tuple[str, str]:
    # logger.info(f"Overriding storage.blob._DEFAULT_CHUNKSIZE --> {storage.blob._DEFAULT_CHUNKSIZE} B")
    # logger.info(f"Overriding storage.blob._MAX_MULTIPART_SIZE --> {storage.blob._MAX_MULTIPART_SIZE} B")
    # logger.info(f"Overriding storage.blob._DEFAULT_TIMEOUT --> {storage.blob._DEFAULT_TIMEOUT} s")

    if not os.path.exists(filename):
        raise FileNotFoundError(filename)

    content_type = mimetypes.MimeTypes().guess_type(filename)[0]

    if key is None:
        key = f"{str(uuid.uuid4())}{os.path.splitext(filename)[-1]}"

    extra_args = {}
    if content_type is not None:
        extra_args["ContentType"] = content_type

    bucket = gs.get_bucket(bucket, timeout=config.GCP_TIMEOUT_SHORT)

    blob = bucket.blob(key)
    blob.upload_from_filename(filename, timeout=config.GCP_TIMEOUT)

    url = None
    if public is True:
        blob.make_public()
        url = blob.public_url

    logger.debug(f"Uploaded {filename} to {bucket}/{key}")

    return key, url


def delete_from_gs(gs, bucket: str, key: str):
    bucket = gs.get_bucket(bucket, timeout=config.GCP_TIMEOUT_SHORT)
    blob = bucket.blob(key)
    blob.delete(timeout=config.GCP_TIMEOUT)

    logger.info("Blob {} deleted.".format(key))


def gs_uri_to_bucket_key(uri: str) -> Tuple[str, str]:
    uri = uri.lstrip("gs://").split("/")
    bucket = uri[0]
    key = "/".join(uri[1:])

    return bucket, key


def gs_bucket_key_to_uri(bucket: str, key: str) -> str:
    return "gs://%s/%s" % (bucket, key)


def gs_bucket_key_to_url(bucket: str, key: str) -> str:
    url = f"https://storage.googleapis.com/{bucket}/{key}"

    return url


def gs_url_to_bucket_key(url: str) -> Tuple[str, str]:
    return gs_uri_to_bucket_key(url.replace("https://storage.googleapis.com/", "gs://"))
