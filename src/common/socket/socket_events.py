from typing import Optional
from src.common.constants import StatusType
from src.common.logger.logger import get_logger
from src.common.socket.socket_publisher import SocketPublisher

logger = get_logger(__name__)


def send_knowledge_extraction_progress(
    socket_publisher: SocketPublisher,
    client_id: int,
    status: StatusType,
    progress: Optional[int] = 0,
    error_message: Optional[str] = None,
):
    assert status is not None, "Invalid status type"
    try:
        request_event = f"KNOWLEDGE_EXTRACTION:PROGRESS:{client_id}"
        message_content = {
            "client_id": int(client_id),
            "chat_message": {"progress": progress, "status": status.name, "error_message": error_message},
            "chat_response_type": "KNOWLEDGE_EXTRACTION_PROGRESS",
        }
        socket_publisher.send(
            event_name=request_event,
            message_content=message_content,
            socket_error_message=None,
        )
    except Exception as e:
        logger.warning(f"Failed to send KNOWLEDGE_EXTRACTION_PROGRESS socket event for client {client_id}, Reason: {e}")
