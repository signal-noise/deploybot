import logging
import os
import hmac
import hashlib
import json
import sys
from datetime import datetime, timedelta

import boto3

from urlparse import parse_qs

COMMAND='/cimon'

ERR_NO_FUNC_FOUND="I didn't understand that, try `%s help`" % COMMAND
HELP_CONTENT="Try `%s setup signal-noise/reponame` to get started..." % COMMAND
ERR_SETUP_PARAM_MISSING="You need to tell me which repo. Try `%s setup username/reponame`" % COMMAND
ERR_SETUP_PARAM_FORMAT=("The repo name should be two parts; the GitHub username and the actual"
    " repository name. e.g. the React library's repo would be `facebook/react`")

SLACK_SIGNING_SECRET_VERSION="v0"

dynamodb = boto3.resource('dynamodb')

logger = logging.getLogger()
if logger.handlers:
    for handler in logger.handlers:
        logger.removeHandler(handler)
logging.basicConfig(level=logging.INFO)

#
#
# Callable user-facing functions
#
#

def help(*args, **kwargs):
    """
    Prints out usage information
    """
    return HELP_CONTENT


def setup(repo=None):
    """
    Initialise project
    """
    if repo is None or repo.strip() == "":
        return ERR_SETUP_PARAM_MISSING

    try:
        (username, repository) = repo.split('/')
    except ValueError as e:
        return ERR_SETUP_PARAM_FORMAT

    return "Setting up %s" % repo


#
#
# Response logic
#
#

def receive(event, context):
    """
    Handler for slash commands sent from Slack
    """
    if not is_request_valid(event):
        logging.error("Authentication Failed")
        return response({"message": "Authentication Failed"}, 401)

    d = parse_qs(event['body'])

    data = {}
    for key, value in d.iteritems():
        data[key] = get_form_variable_value(value)

    if data['command'] not in ['%s' % COMMAND]:
        logging.error("Unexpected command")
        return response({"message": "Unexpected command"}, 500)

    if 'text' not in data or data['text'] == "":
        logging.warn("No text in command")
        data['text'] = 'help'
        
    return slack_response(call_function(data['text']))


def get_form_variable_value(form_var):
    """
    Cleans up submitted form vars on the assumption they are single values
    """
    return form_var[0]


def slack_response(message):
    """
    Builds a data structure for sending a Slack message reply
    """
    return response({
        "response_type": "ephemeral",
        "text": message
    }, 200)


def response(body, status=200):
    """
    Builds the data strcture for an AWS Lambda reply
    """
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
    """
    Takes the `text` of the command and calls a function 
    using the first word as name and the others as parameters, 
    e.g. 'setup myrepo' => setup(myrepo)
    """
    parts = command_text.split()
    f = parts[0]
    p = " ".join(parts[1::])
    try:
        # logging.info('calling func "%s" with [%s]' % (f, ', '.join(map(str, p))))
        return getattr(sys.modules[__name__], f)(p)
    except Exception as e:
        logging.error(e)
        return ERR_NO_FUNC_FOUND


def is_request_valid(event):
    """
    Validates using Signed Secret approach:
    https://api.slack.com/docs/verifying-requests-from-slack
    """
    body = event['body']
    ts = event['headers']['X-Slack-Request-Timestamp']
    slack_signature = event['headers']['X-Slack-Signature']

    # Timestamp must be recent
    now = datetime.now()
    ts_date = datetime.fromtimestamp(int(ts))
    if now - timedelta(minutes=5) > ts_date:
        return False

    basestring = ":".join((SLACK_SIGNING_SECRET_VERSION, ts, body))
    signature = hmac.new(
        os.environ['SLACK_SIGNING_SECRET'],
        basestring,
        digestmod=hashlib.sha256
    ).hexdigest()
    signature = '%s=%s' % (SLACK_SIGNING_SECRET_VERSION, signature)
    
    return hmac.compare_digest(str(signature), str(slack_signature))

