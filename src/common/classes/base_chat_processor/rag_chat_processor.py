from typing import Optional
from langchain_core.chat_history import BaseChatMessageHistory, InMemoryChatMessageHistory
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, HumanMessagePromptTemplate, MessagesPlaceholder, PromptTemplate
from langchain_core.runnables import RunnablePassthrough

from langchain.agents.output_parsers.tools import ToolsAgentOutputParser
from langchain.agents import AgentExecutor
from langchain.agents.format_scratchpad.tools import (
    format_to_tool_messages,
)

from langchain_openai import ChatOpenAI

import openai

from ragas.metrics import context_recall, answer_relevancy, faithfulness
from ragas import evaluate
from ragas.evaluation import Result

from datasets import Dataset


from copy import deepcopy

from src.common.classes.base_chat_processor.constants import AGENT_MAX_ITERATION_ERRORS, LLM_FAILURE_RESPONSE
from src.common.classes.base_chat_processor.exceptions import AgentMaxIterationsException
from src.common.classes.base_chat_processor.history_aware_retriever import (
    ChatHistoryAwareRetriever,
    DEFAULT_HISTORY_AWARE_RETRIEVER_PROMPT,
    DEFAULT_MULTI_QUERY_RETRIEVER_PROMPT,
)
from src.common.logger.logger import get_logger
from src.common.vectorstore.vector_store_service import VectorStoreService
from src.common.constants import VectorType

from src.config import OPENAI_LLM_MODEL

from src.chat.language.utils import Language
from src.chat.text_translation.google_translation_service import GoogleTranslationService

logger = get_logger(__name__)

# QA chain definition - prompt should be aspect to change
QA_SYSTEM_PROMPT = """You are an assistant for question-answering tasks and providing info about brands. \
Use the retrieve_contexts tool to get context needed to answer the question, provide info about marketing guidelines & rules, obtain company policy. \
Follow the rules included in provided contexts! \
If you don't know the answer, just say that you don't know. Make the responses engaging for the user, highlight product features, brand values. Re-use the provided brand context!"""


class RAGChatProcessor(object):
    metrics_history: list[Result] | None = None
    chat_history: BaseChatMessageHistory
    message_handler_db: BaseChatMessageHistory

    """ChatProcessor with retrieval and expanded logs (contexts). RAGAS metrics calculated on the run."""

    def __init__(
        self,
        client_id: int,
        message_handler: BaseChatMessageHistory,
        metrics: list = [context_recall, answer_relevancy, faithfulness],
        model_name: str = OPENAI_LLM_MODEL,
        system_prompt: str = QA_SYSTEM_PROMPT,
        system_prompt_history_aware: str = DEFAULT_HISTORY_AWARE_RETRIEVER_PROMPT,
        system_prompt_multiquery: PromptTemplate = DEFAULT_MULTI_QUERY_RETRIEVER_PROMPT,
        save_metrics: bool = False,
        context_logging: bool = True,
        language: str = "en",
        vectorstore_filter: Optional[any] = None,
    ) -> None:
        self.client_id = client_id

        self.language = language
        self.google_translate_service = GoogleTranslationService()

        self.metrics = metrics
        self.save_metrics = save_metrics

        self.message_handler_db = message_handler
        self.__set_chat_history()

        # Choose the LLM that will drive the agent
        self.llm = ChatOpenAI(model=model_name, temperature=0)
        self.vector_type = VectorType.OPENAI.value
        vector_store_service = VectorStoreService()

        retriever_args = {"k": 5, "score_threshold": 0.2}

        if vectorstore_filter is not None:
            retriever_args["filter"] = vectorstore_filter
        retriever = vector_store_service.get_vector_store_retriever(kwargs=retriever_args)

        retriever_tool = ChatHistoryAwareRetriever()  # type: ignore
        retriever_tool.init_fields(
            llm=self.llm,
            embeddings=vector_store_service.embeddings,
            retriever=retriever,
            messages_handler=self.chat_history,
            context_logging=context_logging,
            system_prompt_history_aware=system_prompt_history_aware,
            system_prompt_multiquery=system_prompt_multiquery,
        )
        self.tools = [retriever_tool]

        qa_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_prompt),
                MessagesPlaceholder("chat_history"),
                MessagesPlaceholder("agent_scratchpad"),
                HumanMessagePromptTemplate(prompt=PromptTemplate(input_variables=["input"], template="{input}")),
            ]
        )

        chain = (
            RunnablePassthrough.assign(agent_scratchpad=lambda x: format_to_tool_messages(x["intermediate_steps"]))
            | qa_prompt
            | self.llm.bind_tools(self.tools)
            | ToolsAgentOutputParser()
        )

        self.rag_chain = AgentExecutor(
            agent=chain,
            tools=self.tools,
            verbose=True,
            return_intermediate_steps=True,
            max_iterations=7,
        )

    def chat(self, human_message_input: str, max_openai_failures: int = 3) -> tuple[str, bool]:
        """Main chat function

        Args:
            human_message_input (str): user input

        Returns:
            tuple[str, bool]: (llm_response, is generation succesfull)
        """
        is_successful_generation = False
        failures_count = 0
        while not is_successful_generation and (failures_count <= max_openai_failures):
            try:
                result = self.rag_chain.invoke(
                    {
                        "input": human_message_input,
                        "chat_history": self.chat_history.messages,
                    }
                )
                if result["output"] in AGENT_MAX_ITERATION_ERRORS:
                    raise AgentMaxIterationsException()
                is_successful_generation = True
            except AgentMaxIterationsException as ae:
                logger.error(f"RAGChatProcessor: chat - AgentMaxIterationsException: {ae}", exc_info=True)
                result = {"output": AgentMaxIterationsException().message}
                break
            except openai.BadRequestError as err:
                logger.info(f"RAGChatProcessor: chat - openai.BadRequestError - retrying: {err}", exc_info=True)
                failures_count += 1
                result = {"output": LLM_FAILURE_RESPONSE}
            except Exception as e:
                logger.error(f"RAGChatProcessor: chat - Error calling Agent Invoke: {e}", exc_info=True)
                failures_count += 1
                result = {"output": LLM_FAILURE_RESPONSE}

        translate_result = self.__translate_text(text=result["output"])

        if self.save_metrics:
            self.__calculate_metrics(result)

        return (translate_result, is_successful_generation)

    def add_message_to_history(self, message: BaseMessage):
        self.message_handler_db.add_message(message)

    def __calculate_metrics(self, state: dict) -> dict:
        # state cannot be touched, deepcopy is needed
        state_ = deepcopy(state)
        state_.pop("intermediate_steps")
        state_.pop("chat_history")

        # convert contexts to strings
        state_["contexts"] = [c[1] for c in state["intermediate_steps"]]

        state_["question"] = state_.pop("input")
        state_["answer"] = state_.pop("output")

        data = Dataset.from_list([state_])
        results = evaluate(dataset=data, metrics=self.metrics, llm=self.llm)

        if self.save_metrics:
            if self.metrics_history is None:
                self.metrics_history = [results]
            else:
                self.metrics_history.append(results)

        logger.info(f"RAGAS Metrics: {results}")

        return state

    def __translate_text(self, text: str) -> str:
        try:
            if self.language == Language.ENGLISH.code:
                logger.debug(
                    """RAGChatProcessor.__translate_text: Skipping translation as the target language is English"""
                )
                return text

            logger.debug(
                f"RAGChatProcessor.__translate_text: Performing translation using Google Translate\n"
                f"Input text: {text}\n"
                f"Target Language: {self.language}"
            )
            translated_text = self.google_translate_service.translate_text(
                contents=[text], target_language_code=self.language
            )
            return translated_text[0]
        except Exception as e:
            logger.error(f"RAGChatProcessor.__translate_text: Force translation failed, Reason: {e}")
        return text

    def __set_chat_history(self):
        chat_history_temp = self.message_handler_db.messages[-50:]
        # Take only last 50 messages to avoid token limit error
        logger.info(
            f"""Chat history set successfully. """
            f"""Truncated {len(self.message_handler_db.messages) - len(chat_history_temp)} """
            f"""messages from the beginning of conversation."""
        )
        self.chat_history = InMemoryChatMessageHistory(messages=chat_history_temp)
