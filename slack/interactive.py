import json
import logging
import os
import hmac
import hashlib
import sys

import boto3
import time
from datetime import datetime, timedelta
from botocore.vendored import requests
from urlparse import parse_qs

FN_RESPONSE_USER_CREATED="Thanks, now I can @ you properly. If there were any other buttons available you should encourage the other channel members to say `hello` to me as well."

ERR_GITHUB_USER_EXISTS="Hm. I have that GitHub username registered to someone else. No action taken, but you can say `goodbye` if you like."
ERR_SLACK_USER_EXISTS="I have you registered against another GitHub username. No action taken, you can say `goodbye` if you like."

SLACK_SIGNING_SECRET_VERSION="v0"

dynamodb = boto3.resource('dynamodb')

logger = logging.getLogger()
if logger.handlers:
    for handler in logger.handlers:
        logger.removeHandler(handler)
logging.basicConfig(level=logging.INFO)


def github_username(gh_user, data=None):
    slack_userid = data['user']['id']
    slack_username = data['user']['name']

    user_table = dynamodb.Table(os.environ['DYNAMODB_TABLE_USER'])

    timestamp = int(time.mktime(datetime.now().timetuple()))
    item = {
        'github_username': gh_user,
        'slack_userid': slack_userid,
        'slack_username': slack_username,
        'createdAt': timestamp,
        'updatedAt': timestamp,
    }
    logging.info("item = {%s}" % ', '.join("%s: %r" % (key,val) for (key,val) in item.iteritems()))
        
    entries = user_table.scan()

    for entry in entries['Items']:
        if (entry['github_username'] == item['github_username'] 
                and entry['slack_userid'] == item['slack_userid']):
            return slack_response(FN_RESPONSE_USER_CREATED)

        if entry['github_username'] == item['github_username']:
            return slack_response(ERR_GITHUB_USER_EXISTS)

        if entry['slack_userid'] == item['slack_userid']:
            return slack_response(ERR_SLACK_USER_EXISTS)

    user_table.put_item(Item=item)

    return slack_response(FN_RESPONSE_USER_CREATED)


#
#
# Response logic
#
#

def receive(event, context):
    """
    Handler for slash interactive events sent from Slack
    """
    if not is_request_valid(event):
        logging.error("Authentication Failed")
        return response({"message": "Authentication Failed"}, 401)

    d = parse_qs(event['body'])

    data = json.loads(d['payload'][0])
    logging.info(data)

    if 'actions' not in data:
        logging.error("Unexpected event")
        return response({"message": "Unexpected event"}, 500)
        
    f = data['actions'][0]['name']
    p = data['actions'][0]['value']
    return getattr(sys.modules[__name__], f)(p, data=data)


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


def slack_response(message, is_public=False):
    """
    Builds a data structure for sending a Slack message reply
    """
    response_type = "ephemeral"
    if is_public is True:
        response_type = "in_channel"

    return response({
        "response_type": "ephemeral",
        "text": message
    }, 200)


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


def get_form_variable_value(form_var):
    """
    Cleans up submitted form vars on the assumption they are single values
    """
    return form_var[0]
