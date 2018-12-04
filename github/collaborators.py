import json
import logging
import os

import jwt
from botocore.vendored import requests

GITHUB_GRAPHQL_URI="https://api.github.com/graphql"

GRAPHQL_QUERY_COLLABORATORS="query {repository(owner:\"%s\", name:\"%s\") { collaborators (first:100) { totalCount nodes { login }}}}"


logger = logging.getLogger()
if logger.handlers:
    for handler in logger.handlers:
        logger.removeHandler(handler)
logging.basicConfig(level=logging.INFO)


def send(event, context):
    http_request = False
    data = event
    if 'body' in data:
        http_request = True
        data = json.loads(event['body'])

    if 'repository' not in data:
        logging.error("Validation Failed")
        raise Exception("Couldn't set up the repository.")
        return

    try:
        (username, repository) = data['repository'].split('/')
    except ValueError as e:
        logging.error("Validation Failed")
        raise Exception("Couldn't set up the repository.")

    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'bearer %s' % os.environ['GITHUB_AUTH_TOKEN']
    }
    uri = 'https://api.github.com/graphql'
    payload = {
        "query": GRAPHQL_QUERY_COLLABORATORS % (username, repository),
    }

    r = requests.post(uri, data=json.dumps(payload), headers=headers)
    json_data = r.json()
    logging.info(json_data)
    response_data = {
        "count": json_data['data']['repository']['collaborators']['totalCount'],
        "collaborators": list(map(
            lambda x: x['login'], 
            json_data['data']['repository']['collaborators']['nodes']
        ))
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
    send({'repository': 'signal-noise/website'}, '')