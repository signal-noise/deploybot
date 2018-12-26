from datetime import datetime, timedelta
import json
import logging
import os
import sys
import time

import boto3
from boto3.dynamodb.conditions import Key

from botocore.vendored import requests

dynamodb = boto3.resource('dynamodb')
lambda_client = boto3.client('lambda', region_name="eu-west-2",)

logger = logging.getLogger()
if logger.handlers:
    for handler in logger.handlers:
        logger.removeHandler(handler)
logging.basicConfig(level=logging.INFO)


#
#
# Event-specific handlers
#
#


def pull_request(data=None):
    """
    Processes PR actions
    """
    action = data['action']
    logging.info('PR action is {}'.format(data['action']))
    if action == 'opened':
        logging.info('create deployment for PR {}'.format(data['number']))
        trigger_github_deployment_create({
            'repository': data['repository']['full_name'],
            'environment': 'pr',
            'number': data['pull_request']['number'],
            'ref': "refs/heads/{}".format(data['pull_request']['head']['ref']),
            'trigger': 'gh_event',
            'commit_author': data['pull_request']['head']['user']['login'],
            'commit_sha': data['pull_request']['head']['sha']
        })
    elif action == 'synchronize':
        logging.info(
            'create deployment for new push to PR {}'.format(data['number']))
        trigger_github_deployment_create({
            'repository': data['repository']['full_name'],
            'environment': 'pr',
            'number': data['pull_request']['number'],
            'ref': "refs/heads/{}".format(data['pull_request']['head']['ref']),
            'trigger': 'gh_event',
            'commit_author': data['pull_request']['head']['user']['login'],
            'commit_sha': data['pull_request']['head']['sha']
        })
    # @TODO action = closed, merged = false
    # should trigger deployment cancel
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

    if env is not None:
        trigger_github_deployment_create({
            'repository': data['repository']['full_name'],
            'environment': env,
            'ref': data['ref'],
            'trigger': 'gh_event',
            'commit_author': data['head_commit']['author']['username'],
            'commit_sha': data['head_commit']['id']
        })
    return


def status(data=None):
    """
    Processes Status update actions - often after these we retry deployments
    """
    state = data['state']
    if state != 'pending':
        logging.info('state of {} is {}'.format(data['context'], state))
        table = dynamodb.Table(os.environ['DYNAMODB_TABLE_DEPLOYMENT'])
        result = table.query(
            IndexName=os.environ['DYNAMODB_TABLE_DEPLOYMENT_BYCOMMIT'],
            KeyConditionExpression=Key('repository').eq(
                data['repository']['full_name']) & Key('commit_sha').eq(data['commit']['sha'])
        )
        logging.info('looking for pending deployment with {} and {}'.format(
            data['repository']['full_name'], data['commit']['sha']))
        if result['Count'] > 0:
            dep = result['Items'][0]
            logging.info('found {}'.format(dep))

            if state == 'success':
                record = {
                    'repository': dep['repository'],
                    'environment': dep['environment'],
                    'ref': dep['ref'],
                    'trigger': dep['trigger'],
                    'commit_author': dep['commit_author_github_login'],
                    'commit_sha': dep['commit_sha']
                }
                if dep['environment'] == 'pr':
                    record['number'] = int(dep['pr'])
                trigger_github_deployment_create(record)
                return
            else:
                logging.info('deleting item from table')
                table.delete_item(Key={
                    'repository': dep['repository'],
                    'id': dep['id']
                })
                return


def deployment(data=None):
    """
    Process Deployment events
    """
    logging.info(data)


#
#
# Shared GitHub functionality
#
#


def create_circleci_deployment(repository, environment, ref, commit_sha, number=None):
    """
    Creates all required params and triggers function
    """
    payload = {
        'repository': repository,
        'environment': environment,
        'version': '{}-{}'.format(environment, commit_sha),
    }
    if environment == 'production':
        payload['tag'] = ref[10:]  # 'refs/tags/XXXX'
        payload['version'] = ref[11:]  # 'refs/tags/vXXXX'
    else:
        payload['revision'] = commit_sha
        if environment == 'pr':
            payload['subdomain'] = 'pr{}'.format(number)
        else:
            payload['subdomain'] = environment

    logging.info('calling cci trigger with {}'.format(payload))
    response = trigger_circleci_trigger(payload)

    # write updated details to DB
    table = dynamodb.Table(os.environ['DYNAMODB_TABLE_DEPLOYMENT'])
    result = table.query(
        IndexName=os.environ['DYNAMODB_TABLE_DEPLOYMENT_BYCOMMIT'],
        KeyConditionExpression=Key('repository').eq(
            repository) & Key('commit_sha').eq(commit_sha)
    )
    if result['Count'] > 0:
        logging.info('found existing record in table: {}'.format(result))
        item = result['Items'][0]
        item['updatedAt'] = int(time.mktime(datetime.now().timetuple()))

        table.update(
            Key={
                'repository': repository,
                'id': item['id']
            },
            UpdateExpression="set deployment_url = :u, build_number = :b",
            ExpressionAttributeValues={
                ':u': response['build_url'],
                ':b': response['build_num']
            },
            ReturnValues="UPDATED_NEW"
        )


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


#
#
# Response logic
#
#


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
    repository = data['repository']['full_name'] if 'repository' in data else None
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
        logging.info("No action taken for event '%s' on repo '%s'" %
                     (event_type, repository))
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


def trigger_github_deployment_create(payload):
    """
    Trigger the function that creates the GH deployment with the given payload
    """
    response = lambda_client.invoke(
        FunctionName="{}-github_deployment_create".format(
            os.environ['FUNCTION_PREFIX']),
        InvocationType='RequestResponse',
        Payload=json.dumps(payload)
    )

    string_response = response["Payload"].read().decode('utf-8')
    parsed_response = json.loads(string_response)
    logging.info(parsed_response)
    return parsed_response


def trigger_circleci_trigger(payload):
    """
    Trigger the function that triggers a CircleCI deployment with the given payload
    """
    response = lambda_client.invoke(
        FunctionName="{}-circleci_trigger".format(
            os.environ['FUNCTION_PREFIX']),
        InvocationType='RequestResponse',
        Payload=json.dumps(payload)
    )

    string_response = response["Payload"].read().decode('utf-8')
    parsed_response = json.loads(string_response)
    logging.info(parsed_response)
    return parsed_response
