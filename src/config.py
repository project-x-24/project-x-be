import os

DEV_STREAMLIT = os.environ.get("DEV_STREAMLIT", "false") == "true"  # Use this flag for dev streamlit

TEST_MODE = os.environ.get("TEST_MODE", "false").lower() == "true"
# Identify the test suite, whether it is other/editor
TEST_SUITE = os.environ.get("TEST_SUITE", "other").lower()
# don't publish to queue if True - will just print out payload
TEST_DUMMY_AMQP_PUBLISH = os.environ.get("TEST_DUMMY_AMQP_PUBLISH", "false").lower() == "true"
USE_DB_POOL = os.environ.get("USE_DB_POOL", "false").lower() == "true"

DB_HOST = os.environ.get("DB_HOST", "")
DB_PORT = os.environ.get("DB_PORT", "")
DB_USERNAME = os.environ.get("DB_USERNAME", "")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "")

REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
REDIS_PORT = int(os.environ.get("REDIS_PORT", 6379))
REDIS_DB = int(os.environ.get("REDIS_DB", 0))
OPENAI_LLM_MODEL = os.environ.get("CHAT_LLM_MODEL", "gpt-4o")
GEMINI_LLM_MODEL = os.environ.get("GEMINI_LLM_MODEL", "gemini-1.5-flash")

AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.environ.get("AWS_REGION")
AWS_S3_BUCKET = os.environ.get("AWS_S3_BUCKET", "pencil-production-bucket")
S3_PUBLIC_ACL = os.environ.get("S3_PUBLIC_ACL", "true") == "true"

# AMQP
RABBIT_URL = os.environ.get("RABBIT_URL", "amqp://guest:guest@localhost:5672?heartbeat=3600")
EXCHANGE_NAME = os.environ.get("EXCHANGE_NAME", "pencil_exchange")
DELAY_EXCHANGE_NAME = os.environ.get("DELAY_EXCHANGE_NAME", "pencil_delay_exchange")
ENABLE_REQUEUE = True
X_MAX_PRIORITY = 255  # We should ideally set it lower: https://www.rabbitmq.com/docs/priority#resource-usage


OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")

# Runtime Environment Identifiers & Logs
LOG_FILE = "bddnai-knowledge-extraction.log"

# R2
R2_ENABLED = os.environ.get("R2_ENABLED", "false") == "true"
R2_ENDPOINT_URL = os.environ.get("R2_ENDPOINT_URL")
R2_ACCESS_KEY_ID = os.environ.get("R2_ACCESS_KEY_ID")
R2_SECRET_ACCESS_KEY = os.environ.get("R2_SECRET_ACCESS_KEY")
R2_REGION = os.environ.get("R2_REGION", "auto")

JWT_SECRET = os.environ.get("JWT_SECRET", "")

API_SERVER_URL = os.environ.get("API_SERVER_URL", "https://localhost:3434")

POLICY_SERVER_URL = os.environ.get("POLICY_SERVER_URL", None)
VISUAL_SERVER_URL = os.environ.get("VISUAL_SERVER_URL", None)
CAMPAIGN_SERVER_URL = os.environ.get("CAMPAIGN_SERVER_URL", None)

# GS
GS_BUCKET = os.environ.get("GS_BUCKET", "pencil-staging-bucket")
GS_PUBLIC_ACL = os.environ.get("GS_PUBLIC_ACL", "true").lower() == "true"
GCP_TIMEOUT = 15 * 60  # 15 mins
GCP_TIMEOUT_SHORT = 5 * 60  # 5 mins

CHAT_PROCESSOR_QUEUE = os.environ.get("CHAT_PROCESSOR_QUEUE", "chat_queue")
CHAT_PROCESSOR_ROUTING_KEY = os.environ.get("CHAT_ROUTING_KEY", "*.chat_processor")
CHAT_DEFAULT_MESSAGE_PRIORITY = int(os.environ.get("CHAT_DEFAULT_MESSAGE_PRIORITY", "100"))

KNOWLEDGE_EXTRACTION_PROCESSOR_QUEUE = os.environ.get(
    "KNOWLEDGE_EXTRACTION_PROCESSOR_QUEUE", "knowledge_extraction_processor_queue"
)
KNOWLEDGE_EXTRACTION_PROCESSOR_ROUTING_KEY = os.environ.get(
    "KNOWLEDGE_EXTRACTION_ROUTING_KEY", "*.knowledge_extraction_processor"
)
KNOWLEDGE_EXTRACTION_PROCESSOR_MESSAGE_PRIORITY = int(
    os.environ.get("KNOWLEDGE_EXTRACTION_PROCESSOR_MESSAGE_PRIORITY", "100")
)

SKIP_TEXT_EDITOR_POST_GENERATION_STEPS = (
    os.environ.get("SKIP_TEXT_EDITOR_POST_GENERATION_STEPS", "false").lower() == "true"
) or DEV_STREAMLIT is True  # Only used for dev streamlit

TEST_MODE = os.environ.get("TEST_MODE", "false").lower() == "true"

OPENAI_LLM_MODEL = os.environ.get("CHAT_LLM_MODEL", "gpt-4o")

GOOGLE_PROJECT_ID = os.environ.get("GOOGLE_PROJECT_ID", None)
VERTEX_VECTOR_STORE_REGION = os.environ.get("VERTEX_VECTOR_STORE_REGION", "europe-west1")
VERTEX_VECTOR_STORE_INDEX_ID = os.environ.get("VERTEX_VECTOR_STORE_INDEX_ID", None)
VERTEX_VECTOR_STORE_ENDPOINT_ID = os.environ.get("VERTEX_VECTOR_STORE_ENDPOINT_ID", None)
VERTEX_VECTOR_STORE_GCS_BUCKET_NAME = os.environ.get("VERTEX_VECTOR_STORE_GCS_BUCKET_NAME", None)
