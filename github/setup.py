import json
import logging
import os

import boto3

from botocore.vendored import requests

GITHUB_GRAPHQL_URI="https://api.github.com/graphql"

dynamodb = boto3.resource('dynamodb')

logger = logging.getLogger()
if logger.handlers:
    for handler in logger.handlers:
        logger.removeHandler(handler)
logging.basicConfig(level=logging.INFO)


def send(event, context):
    data = json.loads(event['body'])
    if 'repository' not in data:
        logging.error("Validation Failed")
        raise Exception("Couldn't set up the repository.")
        return

    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'bearer %s' % os.environ['GITHUB_AUTH_TOKEN']
    }
    uri = 'https://api.github.com/graphql'
    payload = {
        "query": "query { viewer { login }}",
    }

    r = requests.post(uri, data=json.dumps(payload), headers=headers)

    # create a response
    response = {
        "statusCode": r.status_code,
        "body": r.text
    }

    return response


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
    logging.info(response)
    return response