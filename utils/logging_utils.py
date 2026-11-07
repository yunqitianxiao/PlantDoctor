import logging
import functools
from flask import current_app
 
logger = logging.getLogger('PlantDoctor')
 
def log_error(error, context=None):
    msg = f"Error: {str(error)}"
    if context:
        msg += f" | Context: {context}"
    logger.error(msg, exc_info=True)
 
def log_info(message):
    logger.info(message)
 
def log_warning(message):
    logger.warning(message)
 
def handle_exceptions(default_return=None, log_context=None):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                log_error(e, log_context)
                return default_return
        return wrapper
    return decorator
