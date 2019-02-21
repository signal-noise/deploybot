import json
import logging
import os
from datetime import datetime, timedelta
import time

import jwt
from botocore.vendored import requests

CIRCLECI_API_URI = "https://circleci.com/api/v1.1"

logger = logging.getLogger()
if logger.handlers:
    for handler in logger.handlers:
        logger.removeHandler(handler)
logging.basicConfig(level=logging.INFO)
logger.setLevel(logging.INFO)


def send(event, context):
    http_request = False
    data = event
    if 'body' in data:
        http_request = True
        data = json.loads(event['body'])

    if 'repository' not in data:
        logging.error("No 'repository' supplied")
        raise Exception("Couldn't trigger a build.")

    try:
        (username, repository) = data['repository'].split('/')
    except ValueError as e:
        logging.error("Repository name not in right format: {}".format(e))
        raise Exception("Couldn't trigger a build.")

    if 'revision' not in data and 'tag' not in data:
        logging.error("Neither 'revision' nor 'tag' supplied")
        raise Exception("Couldn't trigger a build.")

    if 'environment' not in data:
        logging.error("No 'environment' supplied")
        raise Exception("Couldn't trigger a build.")

    if 'version' not in data:
        logging.error("No 'version' supplied")
        raise Exception("Couldn't trigger a build.")

    headers = {'Content-Type': 'application/json'}
    uri = '%s/project/github/%s/%s?circle-token=%s' % (
        CIRCLECI_API_URI, username, repository, os.environ['CIRCLECI_API_TOKEN'])
    payload = {
        "build_parameters": {
            'ENVIRONMENT': data['environment'],
            'VERSION': data['version']
        }
    }
    if 'revision' in data:
        payload["revision"] = data['revision']
    else:
        payload['tag'] = data['tag']
    if 'subdomain' in data:
        payload["build_parameters"]["SUBDOMAIN"] = data['subdomain']
    if 'url' in data:
        payload["build_parameters"]["URL"] = data['url']

    # https://circleci.com/docs/api/#trigger-a-new-job
    r = requests.post(uri, data=json.dumps(payload), headers=headers)
    json_data = r.json()
    if r.status_code != 200:
        logging.info(json_data)
    response_data = {
        "build_url": json_data['build_url'],
        "build_num": json_data['build_num']
    }

    if http_request:
        response = {
            "statusCode": r.status_code,
            "body": response_data
        }
    else:
        response = response_data

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


if __name__ == "__main__":
    send({'repository': 'signal-noise/deploybot',
          'revision': '6366aefd6dfa0891f89417edf88844667e5f2d55', 'environment': 'test', 'version': '-test-'}, '')
