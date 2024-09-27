from datetime import datetime
from typing import List
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import BaseMessage, messages_from_dict, message_to_dict

from src.common.data_models import models

from src.common.logger.logger import get_logger

logger = get_logger(__name__)


class SqlMessageHistory(BaseChatMessageHistory):
    """Chat message history backed by MySQL."""

    def __init__(self, session_id: int, user_id: int, client_id: int):
        """
        Initialize a new instance of the SqlMessageHistory class.

        """
        self.session_id = session_id
        self.user_id = user_id
        self.client_id = client_id
        self.messages: List[BaseMessage] = []

        self.prepare_data()

    def prepare_data(self) -> None:
        """Prepare the Data."""
        histories = models.ChatHistories.select(models.ChatHistories.message).where(
            models.ChatHistories.session_id == self.session_id, models.ChatHistories.deleted_at.is_null()
        )
        self.messages = messages_from_dict([h.message for h in histories])

    def add_message(self, message: BaseMessage) -> None:
        now = datetime.now()
        self.messages.append(message)
        history = models.ChatHistories()
        history.user_id = self.user_id
        history.client_id = self.client_id
        history.session_id = self.session_id
        history.message = message_to_dict(message)
        history.created_at = now
        history.save()
        logger.info(f"SAVED MESSAGE HISTORY")

    def clear(self) -> None:
        self.messages = []
        models.ChatHistories.delete().where(models.ChatHistories.session_id == self.session_id).execute()
        logger.info(f"SAVED MESSAGE HISTORY:  {self.message_history_type}")
