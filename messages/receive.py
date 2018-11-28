import logging
import os
import json
import sys

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
    # logging.info('validating %s against %s and %s against %s' % (token, os.environ['SLACK_VERIFICATION_TOKEN'], team_id, os.environ['SLACK_TEAM_ID']))
    is_token_valid = token == os.environ['SLACK_VERIFICATION_TOKEN']
    is_team_id_valid = team_id == os.environ['SLACK_TEAM_ID']

    return is_token_valid and is_team_id_valid


def receive(event, context):
    d = parse_qs(event['body'])

    data = {}
    for key, value in d.iteritems():
        data[key] = get_form_variable_value(value)
    logging.info(data)

    if not is_request_valid(data['token'], data['team_id']):
        logging.error("Authentication Failed")
        return slack_response("Authentication Failed", 403)

    if data['command'] not in ['/cimon']:
        logging.error("Unexpected command")
        return slack_response("Unexpected command", 500)

    if 'text' not in data or data['text'] == "":
        logging.error("No text in command")
        data['text'] = 'help'
        
    return slack_response(call_function(data['text']))


def slack_response(message, status=200):
    return response({
        "response_type": "ephemeral",
        "text": message
    }, status)


def response(body, status=200):
    response = {
        "statusCode": int(status),
        "isBase64Encoded": False,
        "headers": { 
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": json.dumps(body)
    }
    logging.info(response)
    return response


def call_function(command_text):
    parts = command_text.split()
    f = parts[0]
    p = parts[1::]
    try:
        logging.info('calling func "%s" with [%s]' % (f, ', '.join(map(str, p))))
        return getattr(sys.modules[__name__], f)(*p)
    except Exception as e:
        logging.error(e)
        return "I didn't understand that, try `/cimon help`"


def help():
    logging.info("Sending help text")
    return 'Try `/cimon setup signal-noise/reponame` to get started...'