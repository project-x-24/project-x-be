from enum import Enum


class LLM(Enum):
    OPENAI_CHATGPT = "openai"
    GOOGLE_PALM2 = "palm"
    GOOGLE_GEMINI = "gemini"


LLM_FAILURE_RESPONSE = "I am unable to process your request at this point in time. Please try after some time."

AGENT_MAX_ITERATION_ERRORS = [
    "Agent stopped due to max iterations.",
    "Agent stopped due to max iterations error.",
    "Agent stopped due to iteration limit or time limit.",
]
