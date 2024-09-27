from dotenv import load_dotenv
from langchain.memory import ChatMessageHistory
import time

from src.common.classes.base_chat_processor.rag_chat_processor import RAGChatProcessor
from src.common.classes.base_chat_processor.history_aware_retriever import ChatHistoryAwareRetriever
from src.common.logger.logger import get_logger

load_dotenv()

logger = get_logger(__name__)
get_logger("langchain.retrievers.multi_query")


def main():

    client_id = 17047
    logger.info(f"Starting new session for CLIENT_ID: {client_id}")
    # using in-memory chat history
    chat_history = ChatMessageHistory()
    chat_server = RAGChatProcessor(client_id, chat_history, context_logging=False)

    retriever: ChatHistoryAwareRetriever = chat_server.tools[0]

    query = "Climachill polo tshirt attributes"

    time_1 = time.time()
    output_1 = retriever.invoke(query)
    logger.info(f"First query: {query} run, time: {time.time() - time_1: .3f}s")

    time_2 = time.time()
    output_2 = retriever.invoke(query)
    logger.info(f"Second query: {query} run, time: {time.time() - time_2: .3f}s")

    query = "Adidas marketing rules"
    time_3 = time.time()
    output_3 = retriever.invoke(query)
    logger.info(f"Different query: {query} run, time: {time.time() - time_3: .3f}s")

    assert output_1 == output_2

if __name__ == "__main__":
    main()
