from enum import Enum, auto
class OutputType(Enum):
    STDOUT = auto()
    STDERR = auto()
    ERROR = auto()
    INFO = auto()
    COMMAND = auto()
    CWD = auto()      # New type for CWD updates