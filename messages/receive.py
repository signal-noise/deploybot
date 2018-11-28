import json
import logging
import os
import time
import uuid

import boto3

from urlparse import parse_qs

dynamodb = boto3.resource('dynamodb')

logger = logging.getLogger()
if logger.handlers:
    for handler in logger.handlers:
        logger.removeHandler(handler)
logging.basicConfig(level=logging.INFO)

def get_form_variable_value(form_var):
    return form_var[0]


def is_request_valid(token, team_id):
    logging.info('validating %s against %s and %s against %s' % (token, os.environ['SLACK_VERIFICATION_TOKEN'], team_id, os.environ['SLACK_TEAM_ID']))
    is_token_valid = token == os.environ['SLACK_VERIFICATION_TOKEN']
    is_team_id_valid = team_id == os.environ['SLACK_TEAM_ID']

    return is_token_valid and is_team_id_valid


def receive(event, context):
    data = parse_qs(event['body'])
    token = get_form_variable_value(data['token'])
    team_id = get_form_variable_value(data['team_id'])
    command = get_form_variable_value(data['command'])
    text = get_form_variable_value(data['text'])

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

    if not is_request_valid(token, team_id):
        logging.error("Authentication Failed")
        response['statusCode'] = 403
        response['body']['attachments'][0]['text'] = "Authentication Failed"
        return

    if len(text) == 0:
        logging.error("No text in command")
        response['statusCode'] = 401
        response['body']['attachments'][0]['text'] = "No text in command - what would you like me to do?"
        return

    if command != 'cimon':
        logging.error("Unexpected command")
        raise Exception("Unexpected command.")
        
    response['body']['text'] = help()
    response['attachments'] = []

    return response

def help():
    return 'Try `/cimon setup signal-noise/reponame` to get started...'