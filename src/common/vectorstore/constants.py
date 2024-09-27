from enum import Enum

class EmbeddingModels(Enum):
    TEXT_EMBEDDING_3_LARGE = "text-embedding-3-large"
    TEXT_EMBEDDING_GECKO_003 = "textembedding-gecko@003"

class EmbeddingVectorSize(Enum):
    TEXT_EMBEDDING_3_LARGE = 3072
    TEXT_EMBEDDING_GECKO_003 = 768

