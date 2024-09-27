from enum import Enum


class VectorType(Enum):
    OPENAI = "openai"


class StatusType(Enum):
    PENDING = 1
    PROGRESS = 2
    FAILURE = 3
    SUCCESS = 4
    BINNED = 5
    TIMEOUT = 6
    PARTIAL_SUCCESS = 7
    VALIDATING = 8
    INVALID = 9
