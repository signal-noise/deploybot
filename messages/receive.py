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


def is_request_valid(token, team_id):
    is_token_valid = token == os.environ['SLACK_VERIFICATION_TOKEN']
    is_team_id_valid = team_id == os.environ['SLACK_TEAM_ID']

    return is_token_valid and is_team_id_valid


def receive(event, context):
    logging.info(event)
    data = json.loads(event['body'])

    response = {
        "statusCode": 200,
        "body": {
            "response_type": "ephemeral",
            "text": "Something went wrong",
            "attachments": [
                {
                    "text":"Partly cloudy today and tomorrow"
                }
            ]
        }
    }

    if not is_request_valid(data['token'], data['team_id']):
        logging.error("Authentication Failed")
        response['statusCode'] = 403
        response['body']['attachments'][0]['text'] = "Authentication Failed"
        return

    if 'text' not in data:
        logging.error("No text in command")
        response['statusCode'] = 401
        response['body']['attachments'][0]['text'] = "No text in command - what would you like me to do?"
        return

    if data['command'] == 'cimon':
        response['body']['text'] = help()
        response['attachments'] = []

    else:
        logging.error("Unexpected command")
        raise Exception("Unexpected command.")


    return response

def help():
    return 'Try `/cimon setup signal-noise/reponame` to get started...'