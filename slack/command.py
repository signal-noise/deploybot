import logging
import os
import hmac
import hashlib
import json
import sys
import time
# import traceback
from datetime import datetime, timedelta
from urlparse import parse_qs

import boto3

COMMAND='/cimon'

FN_RESPONSE_HELP=("There are a few things you can ask me to do. "
    "Try `%s setup signal-noise/reponame` to get started, " 
    "or `%s status` to see what's going on in this channel. "
    "There's `%s hello` to connect your Github and Slack accounts, and `%s bye` to undo that. "
    "There's also `%s reset` if you want to start over on this channel's configuration." % (COMMAND, COMMAND, COMMAND, COMMAND, COMMAND))
FN_RESPONSE_STATUS_EXISTS="This channel is currently set up for `%s`. Some GitHub users aren't yet connected."
FN_RESPONSE_STATUS_NOTEXISTS="This channel hasn't got any configuration at the moment."
FN_RESPONSE_STATUS_ALL_GH_KNOWN="I know all the users oon this repository"
FN_RESPONSE_SETUP="Setting up `%s` in this channel. Note that you won't be able to use this channel for another project, or use that repo in another channel."
FN_RESPONSE_RESET_SUCCESS="Removed this channel's configuration for `%s`"
FN_REPSONSE_HELLO="Hi! Who are you when you're not here?"
FN_REPSONSE_HELLO_NO_UNKNOWNS="Hi! Either we already know each other or you don't have access to the repo this channel is set up for."
FN_RESPONSE_GOODBYE="Who did you say you were again? (Command successful)"
PROMPT_USER_BUTTONS="Select your GitHub username so we can connect it to your Slack username. If you don't see your name you don't have access to the repository"

ERR_NO_FUNC_FOUND="I didn't understand that, try `%s help`. This may also be an error with my code." % COMMAND
ERR_SETUP_PARAM_MISSING="You need to tell me which repo. Try `%s setup username/reponame`" % COMMAND
ERR_SETUP_PARAM_FORMAT=("The repo name should be two parts; the GitHub username and the actual"
    " repository name. e.g. the React library's repo would be `facebook/react`")
ERR_SETUP_CHANNEL_REPO_EXISTS="It looks as though that repo is already setup in this channel"
ERR_SETUP_REPO_EXISTS="That repo is already setup in a different channel. Only one channel per repo."
ERR_SETUP_CHANNEL_EXISTS="This channel is already setup for a different repo. Only one repo per channel."
ERR_RESET_FAILURE="No config found for this channel"
ERR_USER_BUTTON_FALLBACK="You are unable to introduce yourself for some reason. Sorry."
ERR_GOODBYE_NO_USER="Nothing to forget; I couldn't find you in the DB."

SLACK_SIGNING_SECRET_VERSION="v0"

dynamodb = boto3.resource('dynamodb')
lambda_client = boto3.client('lambda', region_name="eu-west-2",)

logger = logging.getLogger()
if logger.handlers:
    for handler in logger.handlers:
        logger.removeHandler(handler)
logging.basicConfig(level=logging.INFO)

#
#
# Callable user-facing functions
#
#

def help(*args, **kwargs):
    """
    Prints out usage information
    """
    return slack_response(FN_RESPONSE_HELP)


def status(text, context):
    """
    Prints out current setup information
    """
    table = dynamodb.Table(os.environ['DYNAMODB_TABLE_PROJECT'])
    entries = table.scan()
    for entry in entries['Items']:
        if entry['slack_channelid'] == context['channel_id']:
            return slack_response(FN_RESPONSE_STATUS_EXISTS % entry['repository'])
    return connect_github_user(FN_RESPONSE_STATUS_NOTEXISTS, entry['repository'], entry['slack_channelid'], FN_RESPONSE_STATUS_ALL_GH_KNOWN)


def setup(repo=None, context=None):
    """
    Initialise project
    """
    logging.info("context = {%s}" % ', '.join("%s: %r" % (key,val) for (key,val) in context.iteritems()))
    if repo is None or repo.strip() == "":
        return slack_response(ERR_SETUP_PARAM_MISSING)

    # @TODO check repo is one word only with a slash in it - does the below properly do that?

    try:
        (username, repository) = repo.split('/')
    except ValueError as e:
        return slack_response(ERR_SETUP_PARAM_FORMAT)

    table = dynamodb.Table(os.environ['DYNAMODB_TABLE_PROJECT'])

    timestamp = int(time.mktime(datetime.now().timetuple()))
    item = {
        'repository': repo,
        'slack_channel': context['channel_name'],
        'slack_channelid': context['channel_id'],
        'createdAt': timestamp,
        'updatedAt': timestamp,
    }
    logging.info("item = {%s}" % ', '.join("%s: %r" % (key,val) for (key,val) in item.iteritems()))
        
    entries = table.scan()
    for entry in entries['Items']:
        if (entry['repository'] == item['repository'] 
                and entry['slack_channelid'] == item['slack_channelid']):
            return slack_response(ERR_SETUP_CHANNEL_REPO_EXISTS)

        if entry['repository'] == item['repository']:
            return slack_response(ERR_SETUP_REPO_EXISTS)

        if entry['slack_channelid'] == item['slack_channelid']:
            return slack_response(ERR_SETUP_CHANNEL_EXISTS)

    table.put_item(Item=item)

    return connect_github_user(FN_RESPONSE_SETUP % repo, item['repository'], item['slack_channelid'])


def reset(text, context):
    """
    Removes any existing configuration for this channel
    """
    table = dynamodb.Table(os.environ['DYNAMODB_TABLE_PROJECT'])
    entries = table.scan()
    for entry in entries['Items']:
        if entry['slack_channelid'] == context['channel_id']:
            table.delete_item(
                Key={
                    'repository': entry['repository'],
                    'slack_channelid': entry['slack_channelid']
                }
            )
            return slack_response(FN_RESPONSE_RESET_SUCCESS % entry['repository'])
    return slack_response(ERR_RESET_FAILURE, True)


def hello(text, context):
    """
    Triggers the GitHub user connection message
    """
    table = dynamodb.Table(os.environ['DYNAMODB_TABLE_PROJECT'])
    entries = table.scan()
    for entry in entries['Items']:
        if context['channel_id'] == entry['slack_channelid']:
            return connect_github_user(FN_REPSONSE_HELLO, entry['repository'], entry['slack_channelid'], FN_REPSONSE_HELLO_NO_UNKNOWNS)


def goodbye(*args, **kwargs):
    """
    Deletes user record of command issuer
    """
    return bye(*args, **kwargs)


def bye(text, context):
    """
    Deletes user record of command issuer
    """
    table = dynamodb.Table(os.environ['DYNAMODB_TABLE_USER'])
    entries = table.scan()
    for entry in entries['Items']:
        if entry['slack_userid'] == context['user_id']:
            table.delete_item(
                Key={
                    'github_username': entry['github_username'],
                    'slack_userid': entry['slack_userid']
                }
            )
            return slack_response(FN_RESPONSE_GOODBYE)
    return slack_response(ERR_GOODBYE_NO_USER)


#
#
# Shared Slack functionality
#
#


def connect_github_user(message, repository, slack_channelid, message_fallback=None):
    response = lambda_client.invoke(
        FunctionName="deploybot-dev-github_collaborators",
        InvocationType='RequestResponse',
        Payload=json.dumps({'repository': repository})
    )

    string_response = response["Payload"].read().decode('utf-8')
    parsed_response = json.loads(string_response)

    table = dynamodb.Table(os.environ['DYNAMODB_TABLE_USER'])
    entries = table.scan()
    gh_users = [ x['github_username'] for x in entries['Items'] ]
    unknown_users = []
    for user in parsed_response['collaborators']:
        if user not in gh_users:
            unknown_users.append(user)

    if len(unknown_users) > 0:
        return slack_user_buttons(
            message, 
            unknown_users,
            "%s:::%s" % (repository, slack_channelid)
        )
    else:
        if message_fallback is not None:
            message = message_fallback
        return slack_response(message)


def slack_response(message, is_public=False):
    """
    Builds a data structure for sending a Slack message reply
    """
    response_type = "ephemeral"
    if is_public is True:
        response_type = "in_channel"

    return response({
        "response_type": "ephemeral",
        "text": message
    }, 200)


def slack_user_buttons(message, github_users, callback_id="abcdef"):
    """
    Builds a data structure to send a message including a button per user
    """
    buttons = list(
        map(
            lambda x: { 
                "name": "github_username",
                "text": "@%s" % x,
                "type": "button",
                "value": x
            },
            github_users
            )
        )
    return response({
        "text": message,
        "attachments": [
            {
                "text": PROMPT_USER_BUTTONS,
                "fallback": ERR_USER_BUTTON_FALLBACK,
                "callback_id": callback_id,
                "color": "#000",
                "attachment_type": "default",
                "actions": buttons
            }
        ]
    }, 200)


def is_request_valid(event):
    """
    Validates using Signed Secret approach:
    https://api.slack.com/docs/verifying-requests-from-slack
    """
    body = event['body']
    ts = event['headers']['X-Slack-Request-Timestamp']
    slack_signature = event['headers']['X-Slack-Signature']

    # Timestamp must be recent
    now = datetime.now()
    ts_date = datetime.fromtimestamp(int(ts))
    if now - timedelta(minutes=5) > ts_date:
        return False

    basestring = ":".join((SLACK_SIGNING_SECRET_VERSION, ts, body))
    signature = hmac.new(
        os.environ['SLACK_SIGNING_SECRET'],
        basestring,
        digestmod=hashlib.sha256
    ).hexdigest()
    signature = '%s=%s' % (SLACK_SIGNING_SECRET_VERSION, signature)
    
    return hmac.compare_digest(str(signature), str(slack_signature))


#
#
# Response logic
#
#

def receive(event, context):
    """
    Handler for slash commands sent from Slack
    """
    if not is_request_valid(event):
        logging.error("Authentication Failed")
        return response({"message": "Authentication Failed"}, 401)

    d = parse_qs(event['body'])

    data = {}
    for key, value in d.iteritems():
        # logging.info('got data "%s"="%s"'%(key, value))
        data[key] = get_form_variable_value(value)

    if data['command'] not in ['%s' % COMMAND]:
        logging.error("Unexpected command")
        return response({"message": "Unexpected command"}, 500)

    if 'text' not in data or data['text'] == "":
        logging.warn("No text in command")
        data['text'] = 'help'

    context = {
        "channel_id": data['channel_id'],
        "channel_name": data['channel_name'],
        "user_id": data['user_id'],
        "user_name": data['user_name'],
        "response_url": data['response_url'],
        "trigger_id": data['trigger_id'],
    }
        
    return call_function(data['text'], context)


def response(body, status=200):
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


def call_function(command_text, context):
    """
    Takes the `text` of the command and calls a function 
    using the first word as name and the others as parameters, 
    e.g. 'setup myrepo' => setup(myrepo)
    """
    parts = command_text.split()
    f = parts[0]
    p = " ".join(parts[1::])
    try:
        # logging.info('calling func "%s" with [%s]' % (f, ', '.join(map(str, p))))
        return getattr(sys.modules[__name__], f)(p, context=context)
    except Exception as e:
        logging.error(e)
        return slack_response(ERR_NO_FUNC_FOUND)


def get_form_variable_value(form_var):
    """
    Cleans up submitted form vars on the assumption they are single values
    """
    return form_var[0]
