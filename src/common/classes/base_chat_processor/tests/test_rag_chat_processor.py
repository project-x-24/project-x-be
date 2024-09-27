import json
from colored import Fore, Style
from dotenv import load_dotenv
from langchain.memory import ChatMessageHistory
import logging
from datetime import datetime
from pydantic import BaseModel
from src.common.classes.base_chat_processor.rag_chat_processor import RAGChatProcessor
from src.common.logger.logger import get_logger

load_dotenv()

logger = get_logger(__name__)
get_logger("langchain.retrievers.multi_query")

fh = logging.FileHandler(f"test_rag_run_{datetime.now().strftime('%d-%m--%H-%M')}.log")
fh.setLevel(logging.INFO)
logger.logger.addHandler(fh)


class RAGTestCase(BaseModel):
    client_id: int
    messages: list[str]


TEST_CASES: list[RAGTestCase] = list(map(lambda x: RAGTestCase.model_validate(x), [
    {
        "client_id": 17047,
        "messages": ["Write me an ecom copy for Adidas Uncontrolled Climachill Polo Shirt", "Great, can you provide me with at least 3 copy suggestions more?"]
    },
    {
        "client_id": 17047,
        "messages": ["Is Adidas able to use the word Sustainable on its copy?"]
    },
    {
        "client_id": 17047,
        "messages": ["Generate headlines for Adidas Ultraboost focusing on environmental credentials."]
    },
    {
        "client_id": 17047,
        "messages": ["write a line of copy for adidas ultraboost emphasising its environmental credentials"]
    },
    {
        "client_id": 17147,
        "messages": ["Create a targeted advertisement for a product or service aimed at Generation Z in India, using the insights from the uploaded documents", "Can you provide where did you source this information?"]
    }
]))

def main():
    assistant_color = f"{Fore.rgb(85, 54, 219)}AI   >>> "
    human_color = f"{Fore.rgb(255, 179, 2)}User >>> "

    for i, test_case in enumerate(TEST_CASES):
        logger.info(f"Starting new session for CLIENT_ID: {test_case.client_id}")
        # using in-memory chat history
        chat_history = ChatMessageHistory()
        chat_server = RAGChatProcessor(test_case.client_id, chat_history, save_metrics=True)
        outputs = []
        for message in test_case.messages:
            logger.info(f"{human_color}{message}{Style.reset}")
            response, __ = chat_server.chat(message)
            outputs.append(response)
            logger.info(f"{assistant_color}{response}{Style.reset}")

        with open(f"{test_case.client_id}_{i}_{datetime.now().strftime('%d-%m--%H-%M')}.json", 'w') as out_file:
            json.dump(
                {
                    **test_case.model_dump(),
                    "outputs": outputs,
                    "metrics": chat_server.metrics_history
                },
                fp=out_file,
                indent=4
            )

if __name__ == "__main__":
    main()
