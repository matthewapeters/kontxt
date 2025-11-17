import logging

from kontxt.json_logger import JsonFormatter

# set the handler for the root logger
logger = logging.getLogger()
handler = logging.StreamHandler()
handler.setFormatter(JsonFormatter())
logger.addHandler(handler)
