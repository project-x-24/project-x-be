from src.common.data_models import models

from src.common.logger.logger import get_logger

logger = get_logger(__name__)


def fetch_model_details(model_id: int = 1):
    try:
        model_details = (
            models.AiModels.select(models.AiModels.id, models.AiModels.metadata, models.AiModels.model_code)
            .where(models.AiModels.id == model_id)
            .dicts()
            .get()
        )
        model_metadata = model_details.get("metadata", {})
        supported_languages = _fetch_supported_languages(model_metadata=model_metadata)
        model_code = model_details.get("model_code", None)

        return {"model_code": model_code, "supported_languages": supported_languages}
    except Exception as e:
        logger.error(f"Failed to fetch ai model details {e}")
        return {"model_code": "gpt-4o", "supported_languages": ["en"]}


def _fetch_supported_languages(model_metadata: dict):
    # Default to English if no supported languages are added
    supported_languages_dict = model_metadata.get("ai_model_supported_languages", {"English": "en"})
    supported_languages = list(supported_languages_dict.values())
    return supported_languages
