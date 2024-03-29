import json
import logging
import os
from datetime import datetime, timedelta
import time
from string import Template

import boto3
from boto3.dynamodb.conditions import Key
import jwt
from botocore.vendored import requests

GITHUB_GRAPHQL_URI = "https://api.github.com/graphql"


dynamodb = boto3.resource('dynamodb', region_name=os.environ['SLS_AWS_REGION'])

logger = logging.getLogger()
if logger.handlers:
    for handler in logger.handlers:
        logger.removeHandler(handler)
logging.basicConfig(level=logging.INFO)
logger.setLevel(logging.INFO)


class RefNotFoundException(Exception):
    pass

    #
    #
    # GitHub GraphQL query generation functions
    #
    #


def get_repo_query(query_vars):
    """
    Builds a GraphQL query to get repo info including refs and
    PR details if provided. The single param is a dict with the
    following keys:
    repoOwner :required
    repoName :required
    refName
    prNumber
    """
    query = """
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
    return {'query': t.substitute(query_vars)}


def get_commitsha_query(query_vars):
    """
    Builds a GraphQL query to get repo info including refs and
    PR details if provided. The single param is a dict with the
    following keys:
    refName
    """
    query = """
        query {
            repository(owner:"$repoOwner", name:"$repoName") {
                ref(qualifiedName:"$refName") {
              		target {
              		    oid
              		}
                },
            }
        }
    """
    t = Template(query)
    return {'query': t.substitute(query_vars)}


def get_create_deployment_mutation(mutation_vars):
    """
    Builds a GraphQL mutation to create a new deployment. The single param
    is a dict with the following keys:
    repoId :required
    refId :required
    environment :required
    description :required
    prNumber
    url
    """
    payload = {}
    if 'prNumber' in mutation_vars and mutation_vars['prNumber'] is not None:
        payload['prNumber'] = mutation_vars.pop('prNumber')
    if 'url' in mutation_vars and mutation_vars['url'] is not None:
        payload['url'] = mutation_vars.pop('url')
    mutation = """
        mutation {
            createDeployment(
                input: {
                    repositoryId: "$repoId",
                    refId: "$refId",
                    environment: "$environment",
                    description: "$description",
                    autoMerge: false,
                    requiredContexts: []
    """
    if payload != {}:
        mutation += """,
                    payload: "$payload"
        """
        payload_str = "{}".format(json.dumps(payload).replace('"', '\\"'))
        # logging.info(payload_str)
        mutation_vars['payload'] = payload_str
    mutation += """
                }
            ) {
                deployment {
                    id,
                    latestStatus {
                        state
                    }
                }
            }
        }
    """
    t = Template(mutation)
    return {'query': t.substitute(mutation_vars)}


def get_create_deployment_status_mutation(mutation_vars):
    """
    Builds a GraphQL mutation to create a new status for an existing
    deployment. The single param is a dict with the following keys:
    deploymentId :required
    state :required
    """
    mutation = """
        mutation {
            createDeploymentStatus(
                input: {
                    deploymentId: "$deploymentId",
                    state: $state
    """
    if 'logUrl' in mutation_vars and mutation_vars['logUrl'] is not None:
        mutation += """,
                    logUrl: "$logUrl"
        """
    if 'environmentUrl' in mutation_vars and mutation_vars['environmentUrl'] is not None:
        mutation += """,
                    environmentUrl: "$environmentUrl"
        """
    mutation += """
                }
            ) {
                deploymentStatus {
                    id
                }
            }
        }
    """
    t = Template(mutation)
    return {'query': t.substitute(mutation_vars)}

#
#
# GitHub query functions
#
#


def get_github_ids(**args):
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
    payload = get_repo_query(args)
    r = requests.post(uri, data=json.dumps(payload), headers=headers)
    json_data = r.json()
    ids = {
        'repoId': json_data['data']['repository']['id'],
        'defaultBranchRefId': json_data['data']['repository']['defaultBranchRef']['id']
    }
    try:
        if 'refName' in args:
            ids['refId'] = json_data['data']['repository']['ref']['id']
        if 'prNumber' in args:
            ids['prId'] = json_data['data']['repository']['pullRequest']['id']
            ids['prHeadRefId'] = json_data['data']['repository']['pullRequest']['headRef']['id']
            ids['prBaseRefId'] = json_data['data']['repository']['pullRequest']['baseRef']['id']
    except TypeError:
        logging.info(json_data)
        raise RefNotFoundException("Does that ref exist?")
    return ids


def get_commitsha_for_ref(repoOwner, repoName, refName):
    """
    Executes an API call based around the repo info query, to return Commit SHA
    of relevant Github objects.
    refName
    """
    # prefix = None
    if refName[0:4] == 'refs':
        parts = refName.split("/")
        refName = "/".join(parts[2:])
        # prefix = "/".join(parts[:2])
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'bearer {}'.format(get_installation_token())
    }
    uri = GITHUB_GRAPHQL_URI
    query_vars = {
        'repoOwner': repoOwner,
        'repoName': repoName,
        'refName': refName
    }
    payload = get_commitsha_query(query_vars)
    logging.info(payload)
    r = requests.post(uri, data=json.dumps(payload), headers=headers)
    json_data = r.json()
    logging.info(json_data)

    try:
        return json_data['data']['repository']['ref']['target']['oid']
    except TypeError:
        raise RefNotFoundException("Does that ref exist?")
    return


def create_deployment(repoId, refId, env, description=None, prNumber=None, url=None):
    """
    Executes an API call based around the createdeployment mutation.
    """
    if description is None:
        description = "Automatically created by SN Deploybot"
    if env == 'pr' and prNumber is not None:
        env = 'pr{}'.format(prNumber)
    headers = {
        'Accept': 'application/vnd.github.flash-preview+json',
        'Content-Type': 'application/json',
        'Authorization': 'bearer {}'.format(get_installation_token())
    }
    uri = GITHUB_GRAPHQL_URI
    payload = get_create_deployment_mutation({
        'repoId': repoId,
        'refId': refId,
        'environment': env,
        'description': description,
        'prNumber': prNumber,
        'url': url
    })

    logging.info(payload)
    r = requests.post(uri, data=json.dumps(payload), headers=headers)
    json_data = r.json()
    logging.info(json_data)
    if json_data['data']['createDeployment']['deployment'] is not None:
        return (True, json_data['data']['createDeployment']['deployment']['id'])
    else:
        return (False, json_data['errors'][0]['message'])


def create_deployment_status(deploymentId, status, logUrl=None, environmentUrl=None, description=None):
    """
    Executes an API call based around the createdeploymentstatus mutation.
    """
    payload = {
        'deploymentId': deploymentId,
        'state': status
    }
    if logUrl is not None:
        payload['logUrl'] = logUrl
    if environmentUrl is not None:
        payload['environmentUrl'] = environmentUrl
    if description is not None:
        payload['description'] = description
    headers = {
        'Accept': 'application/vnd.github.flash-preview+json',
        'Content-Type': 'application/json',
        'Authorization': 'bearer {}'.format(get_installation_token())
    }
    uri = GITHUB_GRAPHQL_URI
    payload = get_create_deployment_status_mutation(payload)

    logging.info(payload)
    r = requests.post(uri, data=json.dumps(payload), headers=headers)
    json_data = r.json()
    logging.info(json_data)
    if json_data['data']['createDeploymentStatus']['deployment'] is not None:
        return (True, json_data['data']['createDeployment']['deployment']['id'])
    else:
        return (False, json_data['errors'][0]['message'])


def get_url_for_env(repo, env, prNumber=None):
    table = dynamodb.Table(os.environ['DYNAMODB_TABLE_PROJECT'])
    entries = table.scan()
    for entry in entries['Items']:
        if entry['repository'] == repo:
            logging.info('get_url found db item {}'.format(entry))
            if 'setting_url' in entry and env in entry['setting_url']:
                return "https://{}".format(entry['setting_url'][env])
            else:
                if 'setting_baseurl' not in entry and 'setting_basedomain' not in entry:
                    logging.warn(
                        "No URL setting found for repo {}".format(repo))
                    return None

                pattern = 'https://{environment}{urlseparator}{basedomain}/'
                separator = '.'
                if env[0:2] == 'pr' and prNumber is not None:
                    env = '{}{}'.format(env, prNumber)

                if 'setting_url_pattern' in entry: # for backward compatibility
                    pattern = entry['setting_url_pattern']
                if 'setting_urlpattern' in entry:
                    pattern = entry['setting_urlpattern']
                if 'setting_url_separator' in entry: # for backward compatibility
                    separator = entry['setting_url_separator']
                if 'setting_urlseparator' in entry:
                    separator = entry['setting_urlseparator']

                # for backward compatibility
                if 'setting_baseurl' in entry and 'setting_basedomain' not in entry:
                    entry['setting_basedomain'] = entry['setting_baseurl']
                if 'setting_url_separator' in entry and 'setting_urlseparator' not in entry:
                    entry['setting_urlseparator'] = entry['setting_url_separator']

                return pattern.format(
                    environment=env,
                    url_separator=separator, # for backward compatibility
                    urlseparator=separator,
                    baseurl=entry['setting_basedomain'], # for backward compatibility
                    basedomain=entry['setting_basedomain'],
                )

    logging.error("No repo {} found in DB for get_url".format(repo))
    return None


def get_installation_token():
    jwt = generate_jwt()

    headers = {
        'Accept': 'application/vnd.github.machine-man-preview+json',
        'Authorization': 'Bearer {}'.format(jwt)
    }
    uri = 'https://api.github.com/app/installations/{}/access_tokens'.format(
        os.environ['GITHUB_APP_INSTALLATIONID'])

    r = requests.post(uri, headers=headers)
    json_data = r.json()

    return json_data['token']


#
#
# Response logic
#
#


def create(event, context):
    """
    Main endpoint for creating GitHub Deployments. Designed to be triggered by another
    function but will work if triggered via HTTP or even locally/directly.
    Expects to be provided with
    repository (e.g. signal-noise/deploybot)
    environment
    ref (or number if environment is PR)
    commit_sha
    """
    http_request = False
    data = event
    logging.info(data)
    if 'body' in data:
        http_request = True
        data = json.loads(event['body'])

    if 'repository' not in data:
        logging.error("Validation Failed")
        raise Exception("Couldn't trigger the deployment.")

    try:
        (username, repository) = data['repository'].split('/')
    except ValueError as e:
        logging.error("Validation Failed {}".format(e))
        raise Exception("Couldn't trigger the deployment.")

    if 'environment' not in data:
        logging.error("Validation Failed")
        raise Exception("Couldn't trigger the deployment.")

    if 'commit_sha' not in data and 'ref' not in data:
        logging.error("no commit SHA, or ref to get one from")
        raise Exception("Couldn't trigger the deployment.")

    env = data['environment'].lower()
    if env not in ('pr', 'preview', 'test', 'staging', 'production'):
        logging.error("%s not a valid environment" % env)
        raise Exception("Couldn't trigger the deployment.")

    if env == 'pr' and 'number' not in data:
        logging.error("no valid PR number")
        raise Exception("Couldn't trigger the deployment.")

    if env != 'pr' and 'ref' not in data:
        logging.error("no valid ref")
        raise Exception("Couldn't trigger the deployment.")

    if 'commit_sha' in data:
        commit_sha = data['commit_sha']
    else:
        commit_sha = get_commitsha_for_ref(username, repository, data['ref'])

    args = {
        "repoOwner": username,
        "repoName": repository
    }
    if env == 'pr':
        prNumber = data['number']
        args['prNumber'] = prNumber
    else:
        prNumber = None
        args['refName'] = data['ref']
    ids = get_github_ids(**args)
    if env == 'pr':
        ids['refId'] = ids['prHeadRefId']
    description = data['description'] if 'description' in data else None

    url = get_url_for_env(data['repository'], env, prNumber)

    table = dynamodb.Table(os.environ['DYNAMODB_TABLE_DEPLOYMENT'])
    timestamp = int(time.mktime(datetime.now().timetuple()))

    # check if we already have an entry for this one, i.e. may be a retry
    result = table.query(
        IndexName=os.environ['DYNAMODB_TABLE_DEPLOYMENT_BYCOMMIT'],
        KeyConditionExpression=Key('repository').eq(
            data['repository']) & Key('commit_sha').eq(commit_sha)
    )
    # if result['Count'] > 0:
    for i in result['Items']:
        if i['environment'] == env:
            item = i
            logging.info('found existing record in table: {}'.format(item))
            item['updatedAt'] = timestamp
            # we're going to write a new record in a moment so we'll delete this now...
            table.delete_item(Key={
                'repository': item['repository'],
                'id': item['id']
            })
            break
    else:
        logging.info(
            'no record with matching repo, commit and env, all results = {}'.format(result))
    # else:
        item = {
            'repository': data['repository'],
            'environment': env,
            'commit_sha': commit_sha,
            'repo_github_id': ids['repoId'],
            'ref_github_id': ids['refId'],
            'url': url,
            'createdAt': timestamp,
            'updatedAt': timestamp,
        }
        if 'ref' in data:
            item['ref'] = data['ref']
        if 'trigger' in data:
            item['trigger'] = data['trigger']
        if 'commit_author' in data:
            item['commit_author_github_login'] = data['commit_author']
        if env == 'pr':
            item['pr'] = data['number']

    success, item['id'] = create_deployment(
        ids['repoId'],
        ids['refId'],
        env,
        prNumber=prNumber,
        url=url,
        description=description
    )

    if success is True:
        item['status'] = 'complete'
        response_data = {
            "deployment_id": item['id']
        }
    else:
        error_message = item['id']
        if 'status checks failed' in item['id']:
            # deployment failed because of incomplete status checks
            item['status'] = 'pending'
            item['id'] = str(timestamp)
        response_data = {
            "error_message": error_message
        }

    logging.info("item = {%s}" % ', '.join("%s: %r" % (key, val)
                                           for (key, val) in item.items()))
    table.put_item(Item=item)

    if http_request:
        response = {
            "statusCode": 200,
            "body": response_data
        }
    else:
        response = response_data

    return response


def create_status(event, context):
    """
    Endpoint for creating new statuses for GitHub Deployments. Designed to be triggered by another
    function but will work if triggered via HTTP or even locally/directly.
    Expects to be provided with
    deploymentId
    status (https://developer.github.com/v4/enum/deploymentstatusstate/)
    """
    http_request = False
    data = event
    logging.info(data)
    if 'body' in data:
        http_request = True
        data = json.loads(event['body'])

    if 'deploymentId' not in data:
        logging.error("no deploymentId")
        raise Exception("Couldn't add a status to the deployment.")
        return

    if 'status' not in data:
        logging.error("no status")
        raise Exception("Couldn't add a status to the deployment.")
        return

    status = data['status'].upper()
    if data['status'] not in ('ERROR', 'FAILURE', 'INACTIVE', 'PENDING', 'SUCCESS'):
        logging.error("status string not valid")
        raise Exception("Couldn't add a status to the deployment.")
        return

    kwargs = {
        "deploymentId": data['deploymentId'],
        "status": status
    }
    if 'logUrl' in data:
        kwargs['logUrl'] = data['logUrl']
    if 'environmentUrl' in data:
        kwargs['environmentUrl'] = data['environmentUrl']
    success, id = create_deployment_status(**kwargs)

    if success is True:
        response_data = {
            "deployment_id": id
        }
    else:
        response_data = {
            "error_message": "Something went wrong :("
        }
    if http_request:
        response = {
            "statusCode": 200,
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
    client = boto3.client('ssm')
    response=client.get_parameter(Name='/deploybot-eu-west-2/prod/github_pk', WithDecryption=True)
    private_key = response['Parameter']['Value']
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


if __name__ == "__main__":
    create({'repository': 'signal-noise/deploybot',
            'environment': 'pr', 'number': 13, 'commit_sha': '880fae856cfd0e6c92f9e4f5e6991768c7c009c0'}, '')
