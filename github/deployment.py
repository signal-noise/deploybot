import json
import logging
import os
from datetime import datetime, timedelta
import time
from string import Template

import jwt
from botocore.vendored import requests

GITHUB_GRAPHQL_URI="https://api.github.com/graphql"


logger = logging.getLogger()
if logger.handlers:
    for handler in logger.handlers:
        logger.removeHandler(handler)
logging.basicConfig(level=logging.INFO)


def getRepoQuery(query_vars):
    """
    Builds a GraphQL query to get repo info including refs and 
    PR details if provided. The single param is a dict with the 
    following keys:
    repoOwner :required 
    repoName :required  
    refName
    prNumber
    """
    query="""
        query {
            repository(owner:"$repoOwner", name:"$repoName") {
                id,
                defaultBranchRef { 
                    id 
                }
    """
    if 'refName' in query_vars:
        query += """,
                ref(qualifiedName:"$refName") {
                    id
                },
        """
    if 'prNumber' in query_vars:
        query += """,
                pullRequest(number: $prNumber) {
                    id,
                    baseRef {
                        id
                    },
                    headRef {
                        id
                    }
                }
        """
    query += """
            }
        }
    """
    t = Template(query)
    return { 'query': t.substitute(query_vars) }


def getCreateDeploymentMutation(mutation_vars):
    """
    Builds a GraphQL mutation to create a new deployment. The single param 
    is a dict with the following keys:
    repoId :required 
    refId :required  
    environment :required 
    description :required 
    url :required 
    """
    mutation = """ 
        mutation { 
            createDeployment( 
                input: {  
                    repositoryId: "$repoId",  
                    refId: "$refId",  
                    environment: "$environment",   
                    description: "$description", 
                    autoMerge: false
                } 
            ) {  
                deployment {
                    id
                } 
            } 
        }
    """
                    # removed from input above: 
                    # payload: {
                    #     url: "$url"
                    # }  
                    # requiredContexts: [] 
    t = Template(mutation)
    return { 'query': t.substitute(mutation_vars) }


def getGitHubIds(**args):
    """
    Executes an API call based around the repo info query, to return NodeIDs 
    of relevant Github objects. 
    repoOwner :required
    repoName : required
    refName
    prNumber
    """
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'bearer {}'.format(get_installation_token()) 
    }
    uri = GITHUB_GRAPHQL_URI
    payload = getRepoQuery(args)
    r = requests.post(uri, data=json.dumps(payload), headers=headers)
    json_data = r.json()
    ids = {
        'repoId': json_data['data']['repository']['id'],
        'defaultBranchRefId': json_data['data']['repository']['defaultBranchRef']['id']
    }
    if 'refName' in args:
        ids['refId'] = json_data['data']['repository']['ref']['id']
    if 'prNumber' in args:
        ids['prId'] = json_data['data']['repository']['pullRequest']['id']
        ids['prHeadRefId'] = json_data['data']['repository']['pullRequest']['headRef']['id']
        ids['prBaseRefId'] = json_data['data']['repository']['pullRequest']['baseRef']['id']
    return ids


def createDeployment(repoId, refId, env, description=None, url=None):
    """
    Executes an API call based around the createdeployment mutation. 
    """
    if description is None:
        description = "Automatically created by SN Deploybot"
    headers = {
        'Accept': 'application/vnd.github.flash-preview+json',
        'Content-Type': 'application/json',
        'Authorization': 'bearer {}'.format(get_installation_token()) 
    }
    uri = GITHUB_GRAPHQL_URI
    payload = getCreateDeploymentMutation({
        'repoId': repoId, 
        'refId': refId, 
        'environment': env, 
        'description': 'a local run test',
        # 'url': 'http://hello.com'
    })

    r = requests.post(uri, data=json.dumps(payload), headers=headers)
    json_data = r.json()
    logging.info(json_data)
    return json_data['data']['createDeployment']['deployment']['id']


def create(event, context):
    """
    Main endpoint for creating GitHub Deployments. Designed to be triggered by another
    function but will work if triggered via HTTP or even locally/directly.
    Expects to be provided with
    repository (e.g. signal-noise/deploybot)
    environment
    ref (or number if environment is PR)
    """
    http_request = False
    data = event
    if 'body' in data:
        http_request = True
        data = json.loads(event['body'])

    if 'repository' not in data:
        logging.error("Validation Failed")
        raise Exception("Couldn't trigger the deployment.")
        return

    if 'environment' not in data:
        logging.error("Validation Failed")
        raise Exception("Couldn't trigger the deployment.")
        return

    try:
        (username, repository) = data['repository'].split('/')
    except ValueError as e:
        logging.error("Validation Failed")
        raise Exception("Couldn't trigger the deployment.")
        return

    # What kind of deployment is this?
    # PR (number)
    # Preview (master branch commit)
    # Staging / Test (release branch commit, different triggers)
    # Production (tag)

    env = data['environment'].lower()
    if env not in ('pr', 'preview', 'test', 'staging', 'production'):
        logging.error("%s not a valid environment" % env)
        raise Exception("Couldn't trigger the deployment.")
        return

    if env == 'pr' and 'number' not in data:
        logging.error("no valid PR number")
        raise Exception("Couldn't trigger the deployment.")
        return

    if env != 'pr' and 'ref' not in data:
        logging.error("no valid ref")
        raise Exception("Couldn't trigger the deployment.")
        return

    args = {
        "repoOwner": username, 
        "repoName": repository
    }
    if env == 'pr':
        args['prNumber'] = data['number']
    else:
        args['refName'] = data['ref']

    ids = getGitHubIds(**args)

    if env == 'pr':
        ids['refId'] = ids['prHeadRefId']

    deployment_id = createDeployment(ids['repoId'], ids['refId'], env)

    response_data = {
        "deployment_id": deployment_id
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


def generate_jwt():
    private_key = os.environ['GITHUB_APP_PK']
    claim = {
        # issued at time
        "iat": int(time.time()),
        # JWT expiration time (10 minute maximum)
        "exp": int(time.time()) + (10 * 60),
        # GitHub App's identifier
        "iss": int(os.environ['GITHUB_APP_ID'])
    }
    token = jwt.encode(
        claim,
        private_key,
        algorithm='RS256')

    return token.decode('utf-8')


def get_installation_token():
    jwt = generate_jwt()

    headers = {
        'Accept': 'application/vnd.github.machine-man-preview+json',
        'Authorization': 'Bearer {}'.format(jwt) 
    }
    uri = 'https://api.github.com/app/installations/{}/access_tokens'.format(os.environ['GITHUB_APP_INSTALLATIONID'])

    r = requests.post(uri, headers=headers)
    json_data = r.json()
 
    return json_data['token']


if __name__ == "__main__":
    create({'repository': 'signal-noise/deploybot', 'environment': 'pr', 'number': 13}, '')