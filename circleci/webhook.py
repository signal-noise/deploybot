import json
import logging
import os

import boto3
from boto3.dynamodb.conditions import Key
lambda_client = boto3.client('lambda', region_name="eu-west-2",)

logger = logging.getLogger()
if logger.handlers:
    for handler in logger.handlers:
        logger.removeHandler(handler)
logging.basicConfig(level=logging.INFO)

dynamodb = boto3.resource('dynamodb')


def receive(event, context):
    """
    Handler for events sent via CircleCI webhook
    """
    data = json.loads(event['body'])
    if 'outcome' not in data['payload']:
        return
    outcome = data['payload']['outcome']

    table = dynamodb.Table(os.environ['DYNAMODB_TABLE_DEPLOYMENT'])
    result = table.query(
        IndexName=os.environ['DYNAMODB_TABLE_DEPLOYMENT_BYBUILDNUM'],
        KeyConditionExpression=Key('repository').eq(
            "{}/{}".format(data['payload']['username'],
                           data['payload']['reponame'])
        ) & Key('build_number').eq(str(data['payload']['build_num']))
    )
    if result['Count'] > 0:
        logging.info(result)
        dep = result['Items'][0]
        logging.info('need to update status of {} to {}'.format(
            dep, outcome))

        if outcome in ('no_tests', ):
            status = 'ERROR'
        elif outcome in ('canceled', 'infrastructure_fail', 'timedout', 'failed'):
            status = 'FAILURE'
        # elif outcome in ():
        #     status = 'INACTIVE'
        # elif outcome in ():
        #     status = 'PENDING'
        elif outcome in ('success', ):
            status = 'SUCCESS'
        payload = {
            "deploymentId": dep['id'],
            "status": status,
            "logUrl": dep['build_url'],
            "environmentUrl": 'https://google.com'  # @TODO URLs!
        }
        response = lambda_client.invoke(
            FunctionName="{}-github_deployment_create_status".format(
                os.environ['FUNCTION_PREFIX']),
            InvocationType='RequestResponse',
            Payload=json.dumps(payload)
        )

        string_response = response["Payload"].read().decode('utf-8')
        parsed_response = json.loads(string_response)
        return parsed_response
