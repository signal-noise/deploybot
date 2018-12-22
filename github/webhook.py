import json
import logging
import os
import sys

import boto3

from botocore.vendored import requests

dynamodb = boto3.resource('dynamodb')

logger = logging.getLogger()
if logger.handlers:
    for handler in logger.handlers:
        logger.removeHandler(handler)
logging.basicConfig(level=logging.INFO)


def pull_request(data=None):
    """
    Processes PR actions
    """
    action = data['action']
    if action == 'opened':
        logging.info('create deployment for PR %s' % data['number'])
        trigger_deployment({
            'repository': data['repository']['full_name'], 
            'environment': 'pr', 
            'number': data['pull_request']['number'],
            'ref': "refs/heads/{}".format(data['pull_request']['head']['ref']),
            'trigger': 'gh_event',
            'commit_author': data['head_commit']['author']['username'],
            'commit_sha': data['head_commit']['id']
        })
    return


def push(data=None):
    """
    Processes Push actions
    """
    env = None

    if data['ref'] == 'refs/heads/master':
        env = 'preview'
    elif data['ref'][:18] == 'refs/heads/release':
        env = 'test'
    elif data['ref'][:11] == 'refs/tags/v':
        env = 'production'
    else:
        # if ref is headref of an open PR
        table = dynamodb.Table(os.environ['DYNAMODB_TABLE_DEPLOYMENT'])
        result = table.query(
            IndexName=os.environ['DYNAMODB_TABLE_DEPLOYMENT_BYREF'],
            KeyConditionExpression=Key('repository').eq(data['repository']['full_name']) & Key('ref').eq(data['ref'])
        )
        logging.info('~~GET REF~~')
        logging.info(result)
        env = 'pr'

    if env is not None:
        trigger_deployment({
            'repository': repository, 
            'environment': env, 
            'ref': data['ref'],
            'trigger': 'gh_event',
            'commit_author': data['head_commit']['author']['username'],
            'commit_sha': data['head_commit']['id']
        })
    return


def is_request_valid(event):
    """
    Validates using Webhook Secret approach:
    https://developer.github.com/webhooks/securing/
    """
    if 'X-Hub-Signature' in event['headers']:
        signature = event['headers']['X-Hub-Signature']
    else:
        # Secret not configured at GH
        return True
    
    # @ToDO implement logic
    return False


def receive(event, context):
    """
    Handler for events sent via GitHub webhook
    """
    if not is_request_valid(event):
        logging.error("Authentication Failed")
        return response({"message": "Authentication Failed"}, 401)

    if 'headers' not in event or 'X-GitHub-Event' not in event['headers']:
        logging.error("Validation Failed")
        raise Exception("Couldn't parse the webhook.")
        return

    data = json.loads(event['body'])
    headers = event['headers']

    event_type = headers['X-GitHub-Event']
    repository = data['repository']['full_name']
    slack_channel = None
    # event_id = headers['X-GitHub-Delivery']

    table = dynamodb.Table(os.environ['DYNAMODB_TABLE_PROJECT'])
    entries = table.scan()
    for entry in entries['Items']:
        if repository == entry['repository']:
            slack_channel = entry['slack_channelid']

    if slack_channel is not None:
        return call_function(event_type, data)
    else:
        logging.info("No action taken for event '%s' on repo '%s'" % (event_type, repository))
        return


def response(body=None, status=200):
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
    return response


def call_function(event_type, data):
    """
    Calls a function using the event_type of the webhook as the 
    name and the whole body as parameters
    """
    try:
        logging.info("Calling %s" % event_type)
        return getattr(sys.modules[__name__], event_type)(data=data)
    except Exception as e:
        logging.error(e)
        return 


def trigger_deployment(payload):
    """
    Trigger the function that creates the GH deployment with the given payload
    """
    response = lambda_client.invoke(
        FunctionName="{}-github_deployment_create".format(os.environ['FUNCTION_PREFIX']),
        InvocationType='RequestResponse',
        Payload=json.dumps(payload)
    )

    string_response = response["Payload"].read().decode('utf-8')
    parsed_response = json.loads(string_response)
    logging.info(parsed_response)
    return parsed_response