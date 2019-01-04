import json
import logging
import os

import boto3

from botocore.vendored import requests

dynamodb = boto3.resource('dynamodb', region_name=os.environ['SLS_AWS_REGION'])

logger = logging.getLogger()
if logger.handlers:
    for handler in logger.handlers:
        logger.removeHandler(handler)
logging.basicConfig(level=logging.INFO)
logger.setLevel(logging.INFO)


def send(event, context):
    http_request = False
    data = event
    if 'body' in data:
        http_request = True
        data = json.loads(event['body'])

    if 'text' not in data:
        logging.error("Validation Failed")
        raise Exception("Couldn't send the message.")
        return

    headers = {'Content-Type': 'application/json'}
    uri = os.environ['SLACK_WEBHOOK_URL']
    channel = os.environ['SLACK_CHANNEL']
    payload = {
        "text": data['text'],
        "channel": channel,
    }

    r = requests.post(uri, data=json.dumps(payload), headers=headers)

    if http_request:
        response = {
            "statusCode": r.status_code,
            "body": r.text
        }
    else:
        response = r.text

    return response


if __name__ == "__main__":
    send({'text': 'local test'}, '')
