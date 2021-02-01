import logging
import sys
from logging.config import dictConfig
from tir.technologies.core.config import ConfigLoader

config = ConfigLoader()

def logger(logger='root'):
    """
    :return:
    """

    if config.smart_test or config.debug_log:
        logging_config = {
            'version': 1,
            'loggers': {
                'root': {  # root logger
                    'level': 'DEBUG',
                    'handlers': ['info_console_handler']
                },
            },
            'handlers': {
                'info_console_handler': {
                    'level': 'DEBUG',
                    'formatter': 'info',
                    'class': 'logging.StreamHandler',
                    'stream': 'ext://sys.stdout',
                },

            },
            'formatters': {
                'info': {
                    'format': '%(asctime)s-%(levelname)s-%(name)s-%(process)d::%(module)s|%(lineno)s:: %(message)s'
                },
            },
        }

    else:

        logging_config = {
            'version': 1,
            'loggers': {
                'root': {  # root logger
                    'level': 'INFO',
                    'handlers': ['debug_console_handler']
                },
            },
            'handlers': {
                'debug_console_handler': {
                    'level': 'INFO',
                    'formatter': 'info',
                    'class': 'logging.StreamHandler',
                    'stream': 'ext://sys.stdout',
                },
            },
            'formatters': {
                'info': {
                    'format': '%(asctime)s-%(levelname)s:: %(message)s'
                },
            },
        }

    dictConfig(logging_config)
    return logging.getLogger(logger)
