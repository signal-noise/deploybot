import json
import logging
import os

import boto3
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource('dynamodb', region_name=os.environ['SLS_AWS_REGION'])
lambda_client = boto3.client(
    'lambda', region_name=os.environ['SLS_AWS_REGION'])

logger = logging.getLogger()
if logger.handlers:
    for handler in logger.handlers:
        logger.removeHandler(handler)
logging.basicConfig(level=logging.INFO)
logger.setLevel(logging.INFO)


def receive(event, context):
    """
    Handler for events sent via CircleCI webhook
    """
    data = json.loads(event['body'])
    if 'outcome' not in data['payload']:
        logging.info("not a final status")
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

        if outcome in ('canceled', 'infrastructure_fail', 'timedout', 'failed'):
            status = 'FAILURE'
        # elif outcome in ():
        #     status = 'INACTIVE'
        # elif outcome in ():
        #     status = 'PENDING'
        elif outcome in ('success', ):
            status = 'SUCCESS'
        else:  # outcome in ('no_tests', ): # or any other outcome
            status = 'ERROR'
        payload = {
            "deploymentId": dep['id'],
            "status": status,
            "logUrl": dep['build_url'],
            "environmentUrl": dep['url']
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

    logging.info(
        "No deployment found matching {}/{} with build number {}".format(data['payload']['username'], data['payload']['reponame'], data['payload']['build_num']))
    return
