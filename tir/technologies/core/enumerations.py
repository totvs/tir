from enum import Enum

class MessageType(Enum):
    '''
    Enumeration that represents the standard messages that are emitted inside log file.

    CORRECT = 1

    INCORRECT = 2

    DISABLED = 3

    ASSERTERROR = 4
    '''
    CORRECT = 1
    INCORRECT = 2
    DISABLED = 3
    ASSERTERROR = 4

class ScrapType(Enum):
    '''
    Enumeration that represents the WebScraping type to be used.

    TEXT = 1

    CSS_SELECTOR = 2

    MIXED = 3

    SCRIPT = 4

    XPATH = 5
    '''
    TEXT = 1
    CSS_SELECTOR = 2
    MIXED = 3
    SCRIPT = 4
    XPATH = 5

class ClickType(Enum):
    '''
    Enumeration that represents the different types of Click logic.

    JS = 1

    SELENIUM = 2

    ACTIONCHAINS = 3
    '''
    JS = 1
    SELENIUM = 2
    ACTIONCHAINS = 3