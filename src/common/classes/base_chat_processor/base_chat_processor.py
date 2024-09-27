from typing import List, Optional

from langchain.agents import (
    AgentExecutor,
    create_tool_calling_agent,
)
from langchain.tools import BaseTool
from langchain.tools.retriever import create_retriever_tool
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, HumanMessagePromptTemplate, MessagesPlaceholder, PromptTemplate
from langchain_openai import ChatOpenAI
from langchain_google_vertexai import ChatVertexAI

from src.common.classes.base_chat_processor.constants import LLM, LLM_FAILURE_RESPONSE
from src.common.logger.logger import get_logger
from src.common.vectorstore.vector_store_service import VectorStoreService
from qdrant_client import models  # type: ignore
from src.common.constants import VectorType
from src.config import OPENAI_LLM_MODEL, GEMINI_LLM_MODEL

logger = get_logger(__name__)


class BaseChatProcessor(object):
    def __init__(
        self,
        client_id: int,
        user_id: int,
        system_prompt: str,
        entity_id: int,
        message_handler: BaseChatMessageHistory,
        custom_tools: Optional[List[BaseTool]] = None,
        model_type: LLM = LLM.OPENAI_CHATGPT.value,
        language: str = "en",
    ) -> None:
        self.user_id = user_id
        self.client_id = client_id
        self.language = language

        self.message_handler = message_handler
        self.prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_prompt),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
                MessagesPlaceholder(variable_name="chat_history", optional=True),
                HumanMessagePromptTemplate(prompt=PromptTemplate(input_variables=["input"], template="{input}")),
            ]
        )

        # Uncomment this to use retriever
        # Remove rag from agent for for as its not being used any chat to ads agnet"
        # if model_type == LLM.OPENAI_CHATGPT.value:
        #     self.vector_type = VectorType.OPENAI.value
        # elif model_type == LLM.GOOGLE_PALM2.value or model_type == LLM.GOOGLE_GEMINI.value:
        #     self.vector_type = VectorType.GOOGLE.value
        # else:
        #     raise RuntimeError(f"Failed to resolve which vector type to use for LLM - {model_type}")
        # collection_name = str(self.client_id) + "_" + f"{self.vector_type}"
        # vector_store_service = VectorStoreService(collection_name=collection_name, vector_type=self.vector_type)

        # filter = models.Filter(
        #     should=[
        #         models.FieldCondition(key="metadata.entity_id", match=models.MatchValue(value=str(entity_id))),
        #         models.IsEmptyCondition(
        #             is_empty=models.PayloadField(key="metadata.entity_id"),
        #         ),
        #     ]
        # )

        # retriever = vector_store_service.get_vector_store_retriever(
        #     kwargs={"k": 2, "score_threshold": 0.2, "filter": filter}
        # )

        # self.retriver_tool = create_retriever_tool(
        #     retriever,
        #     "user_provided_document_data",
        #     """
        #     Searches and returns excerpts from user provided documents.
        #     """,
        # )

        self.tools = []  # self.retriver_tool
        if custom_tools is not None and isinstance(custom_tools, list):
            self.tools.extend(custom_tools)

        # Choose the LLM that will drive the agent
        if model_type == LLM.OPENAI_CHATGPT.value:
            self.llm = ChatOpenAI(model=OPENAI_LLM_MODEL, temperature=0)

        elif model_type == LLM.GOOGLE_GEMINI.value or model_type == LLM.GOOGLE_PALM2.value:
            self.llm = ChatVertexAI(model_name=GEMINI_LLM_MODEL, convert_system_message_to_human=False, temperature=0)
        else:
            raise ValueError(f"Invalid model_type: {model_type}")

        self.agent = create_tool_calling_agent(self.llm, self.tools, self.prompt)
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            max_iterations=5,
            verbose=False,
            return_intermediate_steps=False,
        )

    def chat(
        self,
        human_message_input: str,
        history_messages: Optional[List[BaseMessage]] = None,
        skip_saving_history: bool = False,
    ):
        if history_messages is None:
            history_messages = self.message_handler.messages

        try:
            result = self.agent_executor.invoke(
                {
                    "input": human_message_input,
                    "chat_history": history_messages,
                }
            )
        except Exception as e:
            logger.error(f"BaseChatProcessor: chat - Error calling Agent Invoke: {e}", exc_info=True)
            result = {"output": LLM_FAILURE_RESPONSE}

        if skip_saving_history is False:
            human_message = HumanMessage(content=result["input"])
            ai_message = AIMessage(content=result["output"])
            self.add_message_to_history(human_message)
            self.add_message_to_history(ai_message)

        return result

    def add_message_to_history(self, message: BaseMessage):
        self.message_handler.add_message(message)
