import json
import logging
import os
import time
import uuid

import boto3

from botocore.vendored import requests

dynamodb = boto3.resource('dynamodb')

logger = logging.getLogger()
if logger.handlers:
    for handler in logger.handlers:
        logger.removeHandler(handler)
logging.basicConfig(level=logging.INFO)


def send(event, context):
    data = json.loads(event['body'])
    if 'text' not in data:
        logging.error("Validation Failed")
        raise Exception("Couldn't send the message.")
        return

    uri = os.environ['SLACK_WEBHOOK_URL']
    channel = os.environ['SLACK_CHANNEL']
    payload = {
        "text": data['text'],
        "channel": channel,
    }

    r = requests.post(uri, data=payload)

    # create a response
    response = {
        "statusCode": r.status_code,
        "body": r.text
    }

    return response
