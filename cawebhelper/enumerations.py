from enum import Enum

class MessageType(Enum):
    '''
    Enumeration that represents the standard messages that are emitted inside log file.
    '''
    CORRECT = 1
    INCORRECT = 2
    DISABLED = 3
    ASSERTERROR = 4 