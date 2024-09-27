import requests
from src.common.logger.logger import get_logger
from src.config import POLICY_SERVER_URL

logger = get_logger(__name__)

DEFAULT_AVAILABLE_QUOTA = 10


def get_project(project_id: int):
    try:
        # project_row = cm.ProjectMetadata.get_by_id(project_id)
        project_row = None  # Fix later when the db is available
        return project_row
    except Exception as e:
        raise RuntimeError(f"Failed to get project for id: {project_id}")


def debit_generation_quota(project_id: int, debit_count: int, jwt_token: str, metadata: dict = {}):
    try:
        project = get_project(project_id=project_id)

        endpoint = POLICY_SERVER_URL + "/api/generation/count-log"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {jwt_token}",
        }
        payload = {
            "projectUuid": project.project_uuid,
            "projectTypeId": project.project_type_id,
            "debits": debit_count,
            "metadata": metadata,
        }
        response = requests.post(endpoint, json=payload, headers=headers)
        response.raise_for_status()
        logger.info(f"SUCESSFULLY debitted quota:{debit_count} for generation from project_id:{project_id}")
    except Exception as e:
        logger.error(f"ERROR DEBITTING GENERATION QUOTA: {e}. PROCEEDING WITHOUT ACCOUNTING IT!!!", exc_info=True)


def get_generation_quota(jwt_token: str):
    try:

        endpoint = POLICY_SERVER_URL + "/api/ads/quota"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {jwt_token}",
        }
        response = requests.get(endpoint, headers=headers)
        response.raise_for_status()
        result = response.json()

        available_quota = result.get("generation", {}).get("availableCredits")
        return available_quota
    except Exception as e:
        logger.error(f"ERROR GETTING GENERATION QUOTA: {e}. PROCEEDING WITHOUT ACCOUNTING IT!!!", exc_info=True)
        return DEFAULT_AVAILABLE_QUOTA
