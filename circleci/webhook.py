import json
import logging
import os

import boto3
from boto3.dynamodb.conditions import Key

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
    logging.info(data)

    table = dynamodb.Table(os.environ['DYNAMODB_TABLE_DEPLOYMENT'])
    result = table.query(
        IndexName=os.environ['DYNAMODB_TABLE_DEPLOYMENT_BYBUILDNUM'],
        KeyConditionExpression=Key('repository').eq(
            "{}/{}".format(data['payload']['username'],
                           data['payload']['reponame'])
        ) & Key('build_number').eq(data['payload']['build_num'])
    )

    logging.info(result)
