import logging
import time
from logging.config import dictConfig
from tir.technologies.core.config import ConfigLoader
from datetime import datetime
from pathlib import Path
import os
import socket
import inspect
import sys

filename = None
folder = None
file_path = None
config = None
_logger = None

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

def create_folder():
    """

    :return:
    """

    path = None
    folder_path = None
    error = None

    try:
        if config.log_http:
            folder_path = Path(config.log_http, config.country, config.release, config.issue,config.execution_id, get_file_name('testsuite'))
            os.makedirs(Path(folder_path))
        elif config.log_folder:
            folder_path = Path(config.log_folder)
            os.makedirs(Path(folder_path))
        else:
            path = Path("/tmp/Log", socket.gethostname()) if sys.platform.startswith('linux') else Path("Log", socket.gethostname())
            os.makedirs(path)
    except Exception as e:
        error = e

    if folder_path:
        path = str(Path(folder_path))

    if os.path.isdir(path):
        return str(path)
    else:
        raise Exception(f"Folder path not found: {path}: {str(error)}")	

def create_file():
    """
    Creates an empty file before logger
    [Internal]

    """

    today = datetime.today()

    filename = f"TIR_{get_file_name('testsuite')}_{today.strftime('%Y%m%d%H%M%S%f')[:-3]}.log"

    folder = create_folder()

    success = False

    error = None

    endtime = time.time() + config.time_out
    while (time.time() < endtime and not success):
        try:
            with open(Path(folder, filename), "w", ):
                return str(Path(folder, filename))
        except Exception as e:
            time.sleep(5)
            error = str(e)
            print(error)
    
    if error:
        return error

def configure_logger():
    """
    :return:
    """

    global _logger
    global filename
    global folder
    global file_path
    global config

    config = ConfigLoader()

    if not config._json_data:
        return

    logger_profile = 'user_console'

    if config.debug_log:
        logger_profile = 'root'
    else:
        logger_profile = 'debug_console' if config.smart_test else logger_profile

    if logger_profile == 'root':
        file_path = create_file()

    logging_config = {
        'version': 1,
        'formatters': {
            'debug': {
                'format': '%(asctime)s-%(levelname)s-%(name)s-%(process)d::%(module)s::%(funcName)s|%(lineno)s:: %(message)s'
            },
            'info':{
                'format': '%(asctime)s-%(levelname)s:: %(message)s'
            }
        },
        'handlers': {
            'debug_console_handler': {
                'level': 'DEBUG',
                'formatter': 'debug',
                'class': 'logging.StreamHandler',
                'stream': 'ext://sys.stdout',
            },
            'info_console_handler': {
                'level': 'INFO',
                'formatter': 'info',
                'class': 'logging.StreamHandler',
                'stream': 'ext://sys.stdout',
            }
        },
        'loggers': {
            'root': {  # root logger
                'level': 'DEBUG',
                'handlers': ['debug_console_handler']
            },
            'debug_console': {  # console logger
                'level': 'DEBUG',
                'handlers': ['debug_console_handler']
            },
            'user_console': {  # user console logger
                'level': 'INFO',
                'handlers': ['info_console_handler']
            },
        },
    }

    if file_path and os.path.exists(file_path):
        logging_config['handlers']['memory_handler'] = {
            'level': 'DEBUG',
            'formatter': 'debug',
            'class': 'logging.handlers.MemoryHandler',
            'capacity': 5*1024*1024,
            'flushLevel': logging.CRITICAL,
            'target': 'debug_file_handler'
        }
        logging_config['handlers']['debug_file_handler'] = {
            'level': 'DEBUG',
            'formatter': 'debug',
            'class': 'logging.FileHandler',
            'filename': file_path,
            'mode': 'a'
        }
        logging_config['loggers']['root']['handlers'].append('memory_handler')
        logging_config['loggers']['root']['handlers'].append('debug_file_handler')

    dictConfig(logging_config)
    _logger = logging.getLogger(logger_profile)
    _logger.propagate = False

def logger():
    global _logger
    if _logger is None:
        configure_logger()
        _logger.debug(f"Log file created: '{file_path}'")
    return _logger
