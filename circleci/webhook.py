import json
import logging

logger = logging.getLogger()
if logger.handlers:
    for handler in logger.handlers:
        logger.removeHandler(handler)
logging.basicConfig(level=logging.INFO)


def receive(event, context):
    """
    Handler for events sent via CircleCI webhook
    """

    data = json.loads(event['body'])
    logging.info(data)
