from typing import Type, Optional

from langchain.callbacks.manager import CallbackManagerForToolRun

from langchain_core.tools import BaseTool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder, PromptTemplate
from langchain_core.vectorstores import VectorStoreRetriever
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.documents import Document
from langchain_core.runnables import Runnable
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.embeddings import Embeddings

from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.multi_query import MultiQueryRetriever
from langchain.retrievers.document_compressors import EmbeddingsFilter
from langchain.chains.history_aware_retriever import create_history_aware_retriever
from langchain_community.document_transformers.long_context_reorder import LongContextReorder
from langchain.pydantic_v1 import BaseModel, Field

from src.common.logger.logger import get_logger

logger = get_logger(__name__)

DEFAULT_HISTORY_AWARE_RETRIEVER_PROMPT = """Given a chat history and the latest user input \
        which might reference context in the chat history, formulate a standalone question \
        which can be understood without the chat history. \
        Do NOT answer the question, \
        just reformulate it if needed and otherwise return it as is."""

DEFAULT_MULTI_QUERY_RETRIEVER_PROMPT = PromptTemplate(
    input_variables=["question"],
    template="""Your task is to generate 3 different versions of the given user
        input to retrieve relevant documents from a vector database.
        Database contains info about products, brand, marketing policy, company policy, guidelines etc.
        Try to cover all possible options, \
        by generating multiple perspectives on the user question,
        your goal is to help the user overcome some of the limitations
        of distance-based similarity search. Provide these alternative
        questions separated by newlines. Original question: {question}""",
)


class ChatHistoryAwareRetrieverInput(BaseModel):
    input: str = Field(description="User input, should be in a form of a question")


class ChatHistoryAwareRetriever(BaseTool):
    name = "retrieve_contexts"
    description = "Retrieves context relevant to given input. Essential for getting info about brand and products!!!"
    args_schema: Type[BaseModel] = ChatHistoryAwareRetrieverInput

    llm: BaseChatModel | None = None
    embeddings: Embeddings | None = None
    messages_handler: BaseChatMessageHistory | None = None
    chain: Runnable | None = None
    verbose: bool = False

    cache: dict[str, list[Document]] = {}

    def init_fields(
        self,
        llm: BaseChatModel,
        embeddings: Embeddings,
        retriever: VectorStoreRetriever,
        messages_handler: BaseChatMessageHistory,
        system_prompt_multiquery: PromptTemplate = DEFAULT_MULTI_QUERY_RETRIEVER_PROMPT,
        system_prompt_history_aware: str = DEFAULT_HISTORY_AWARE_RETRIEVER_PROMPT,
        context_logging: bool = False,
    ):

        self.llm = llm
        self.embeddings = embeddings
        self.messages_handler = messages_handler
        self.verbose = context_logging

        multi_retriever = MultiQueryRetriever.from_llm(
            retriever=retriever, llm=self.llm, prompt=system_prompt_multiquery
        )

        compression_retriever = ContextualCompressionRetriever(
            base_compressor=EmbeddingsFilter(embeddings=self.embeddings, similarity_threshold=0.0),
            base_retriever=multi_retriever,
        )

        contextualize_q_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_prompt_history_aware),
                MessagesPlaceholder("chat_history"),
                ("human", "{input}"),
            ]
        )

        self.chain = create_history_aware_retriever(self.llm, compression_retriever, contextualize_q_prompt)

    def _run(self, input: str, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        logger.info(f"Invoking retrieve_contexts with input: {input}")

        # Cache hitting 'agent stopped due to max iterations error'. Ajai or Jan TODO: Investigate

        # if len(input) and (input in self.cache):
        #     logger.info(f"Invoking retrieve_contexts with input [USING CACHE]: {input}")
        #     docs = self.cache[input]
        # else:
        #     logger.info(f"Invoking retrieve_contexts with input [USING RETRIEVAL]: {input}")
        #     if any(map(lambda x: x is None, (self.llm, self.messages_handler, self.chain))):
        #         raise ValueError("init_fields has to be used before tool call")
        #     else:
        #         docs = self.chain.invoke({"input": input, "chat_history": self.messages_handler.messages})

        #         docs = list(LongContextReorder().transform_documents(docs))

        #     self.cache[input] = docs

        logger.info(f"Invoking retrieve_contexts with input [USING RETRIEVAL]: {input}")
        if any(map(lambda x: x is None, (self.llm, self.messages_handler, self.chain))):
            raise ValueError("init_fields has to be used before tool call")
        else:
            docs = self.chain.invoke({"input": input, "chat_history": self.messages_handler.messages})

            docs = list(LongContextReorder().transform_documents(docs))

        if self.verbose:
            self.log_context(docs)

        return self.parse_output(docs)

    def _arun(self, input: str) -> str:
        raise NotImplementedError("ChatHistoryAwareRetriever does not support async")

    @staticmethod
    def parse_output(docs: list[Document]) -> str:
        if len(docs) < 1:
            return "No relevant documents found"
        return "\n".join(d.page_content for d in docs)

    @staticmethod
    def log_context(docs: list[Document]) -> None:
        try:
            for i, doc in enumerate(docs):
                logger.info(
                    f"CONTEXT on position: {i} -- {doc.metadata.get('document_type', 'None')}:{doc.metadata.get('asset_id', 'None')} -- PAGE: {doc.metadata.get('page_number', 'None')}"
                )
                logger.info(doc.page_content)
        except Exception as e:
            logger.error(f"Error while logging context: {e}")
            pass
