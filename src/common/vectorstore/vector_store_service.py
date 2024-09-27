from typing import Optional
from langchain_openai import OpenAIEmbeddings
from src.common.vectorstore.constants import EmbeddingModels, EmbeddingVectorSize
from langchain_core.vectorstores import VectorStoreRetriever
from langchain_google_vertexai import (
    VectorSearchVectorStore,
)
from src.config import (
    GOOGLE_PROJECT_ID,
    VERTEX_VECTOR_STORE_REGION,
    VERTEX_VECTOR_STORE_ENDPOINT_ID,
    VERTEX_VECTOR_STORE_INDEX_ID,
    VERTEX_VECTOR_STORE_GCS_BUCKET_NAME,
)


class VectorStoreService:
    def __init__(self) -> None:
        self.embedding_model = EmbeddingModels.TEXT_EMBEDDING_3_LARGE.value
        self.vector_size = EmbeddingVectorSize.TEXT_EMBEDDING_3_LARGE.value
        self.embeddings = OpenAIEmbeddings(model=self.embedding_model)

        self.vector_store = VectorSearchVectorStore.from_components(
            project_id=GOOGLE_PROJECT_ID,
            region=VERTEX_VECTOR_STORE_REGION,
            gcs_bucket_name=VERTEX_VECTOR_STORE_GCS_BUCKET_NAME,
            index_id=VERTEX_VECTOR_STORE_INDEX_ID,
            endpoint_id=VERTEX_VECTOR_STORE_ENDPOINT_ID,
            embedding=self.embeddings,
            stream_update=True,
        )

    def get_vector_store_retriever(self, kwargs: Optional[dict] = None) -> VectorStoreRetriever:
        return self.vector_store.as_retriever(search_type="similarity", search_kwargs=kwargs)
