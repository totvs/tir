import logging
import sys
from logging.config import dictConfig
from tir.technologies.core.config import ConfigLoader
from datetime import datetime
import inspect

config = ConfigLoader()

filename = None

def logger(logger='root'):
    """
    :return:
    """

    global filename

    today = datetime.today()

    if not filename:
        filename = f"TIR_{get_file_name('testsuite')}_{today.strftime('%Y%m%d%H%M%S%f')[:-3]}.log"

    if config.smart_test or config.debug_log:
        logging_config = {
            'version': 1,
            'loggers': {
                'root': {  # root logger
                    'level': 'DEBUG',
                    'handlers': ['debug_console_handler', 'debug_file_handler']
                },
            },
            'handlers': {
                'debug_console_handler': {
                    'level': 'DEBUG',
                    'formatter': 'info',
                    'class': 'logging.StreamHandler',
                    'stream': 'ext://sys.stdout',
                },
                'debug_file_handler': {
                    'level': 'DEBUG',
                    'formatter': 'info',
                    'filename': filename,
                    'class': 'logging.FileHandler',
                    'mode': 'a'
                },
            },
            'formatters': {
                'info': {
                    'format': '%(asctime)s-%(levelname)s-%(name)s-%(process)d::%(module)s::%(funcName)s|%(lineno)s:: %(message)s'
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

def get_file_name(file_name):
    """
    Returns a Testsuite name
    """
    testsuite_stack = next(iter(list(filter(lambda x: file_name in x.filename.lower(), inspect.stack()))), None)

    if testsuite_stack:

        if '/' in testsuite_stack.filename:
            split_character = '/'
        else:
            split_character = '\\'

        return testsuite_stack.filename.split(split_character)[-1].split(".")[0]
    else:
        return ""