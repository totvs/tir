from enum import Enum

class MessageType(Enum):
    '''
    Enumeration that represents the standard messages that are emitted inside log file.
    '''
    CORRECT = 1
    INCORRECT = 2
    DISABLED = 3
    ASSERTERROR = 4

class ScrapType(Enum):
    '''
    Enumeration that represents the WebScraping type to be used.
    '''
    UNKNOWN = 1
    TEXT = 2
    CSS_SELECTOR = 3
    MIXED = 4
    SCRIPT = 5
    XPATH = 6