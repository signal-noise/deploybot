import logging
import os
import hmac
import hashlib
import json
import sys
import time
# import traceback
from datetime import datetime, timedelta
from urllib.parse import parse_qs

import boto3

COMMAND = os.environ['COMMAND']

SET_OPTIONS = {
        "basedomain": "basedomain",
        "urlpattern": "urlpattern",
        "urlseparator": "urlseparator",
        "url": "url"
    }

FN_RESPONSE_HELP = ("There are a few things you can ask me to do. "
                    "Try `%s setup signal-noise/reponame` to get started, "
                    "or `%s get` to see what's going on in this channel. "
                    "There's `%s hello` to connect your Github and Slack accounts, and `%s bye` to undo that. "
                    "There's also `%s reset` if you want to start over on this channel's configuration."
                    "To see information about setting variables, try `%s set`" % (COMMAND, COMMAND, COMMAND, COMMAND, COMMAND, COMMAND))
FN_RESPONSE_SET = ("Call this with two or three arguments; e.g. `%s set basedomain test.com`, or `%s set URL preview preview.test.com`. "
                   "Settings you can set here are: \n"
                   "- `url`: A domain specific to an environment, to override the *urlpattern* rule. You must call this with the environment name and then the FQDN as above. Please don't include protocol but DO ensure HTTPS is supported.\n"
                   "- `urlpattern`: The pattern used to generate URLs for environments. Defaults to `https://{environment}{urlseparator}{basedomain}/`. Please include all those 3 variables in that format.\n"
                   "- `basedomain`: The domain: if your PR environment is at `https://pr27.test.com`, this is `test.com`. This will be used to create all environment URLs not explicitly specified.\n"
                   "- `urlseparator`: The character used to join your specific environment name to the basedomain. I.e. in `https://pr27.test.com`, the `.` between `pr27` and `test.com`. Defaults to `.` " % (COMMAND, COMMAND))
FN_RESPONSE_SET_CONFIRM = "Great, I've set %s to %s."
FN_RESPONSE_UNSET = "Call this with the one or two arguments you called `set` with, and no value part - e.g. `%s unset basedomain`" % COMMAND
FN_RESPONSE_GET_EXISTS = "This channel is currently set up for `%s` \nbasedomain: `%s` \n url: `%s` \n urlpattern: `%s` \n urlseparator: `%s` \n Some GitHub users may not be connected."
FN_RESPONSE_GET_NOTEXISTS = "This channel hasn't got any configuration at the moment."
FN_RESPONSE_GET_ALL_GH_KNOWN = "I know all the users on this repository"
FN_RESPONSE_SETUP = "Setting up `%s` in this channel. Note that you won't be able to use this channel for another project, or use that repo in another channel. You should run `set` to get your environment URLs configured."
FN_RESPONSE_RESET_SUCCESS = "Removed this channel's configuration for `%s`"
FN_RESPONSE_HELLO = "Hi! Who are you when you're not here?"
FN_RESPONSE_HELLO_NO_UNKNOWNS = "Hi! Either we already know each other or you don't have access to the repo this channel is set up for."
FN_RESPONSE_GOODBYE = "Who did you say you were again? (Command successful)"
FN_RESPONSE_DEPLOY = "Deployment of `%s` to `%s` has started!"
PROMPT_USER_BUTTONS = "Select your GitHub username so we can connect it to your Slack username. If you don't see your name you don't have access to the repository"

ERR_NO_FUNC_FOUND = "I didn't understand that, try `%s help`. This may also be an error with my code." % COMMAND
ERR_SET = "Something went wrong. Have you set this channel up with a repo yet?"
ERR_SET_SETTING_NOT_RECOGNISED = "I didn't recognise that setting. "
ERR_SET_SETTING_2_ARGS = "That setting needs a single value; unset with just the setting name. "
ERR_SET_SETTING_3_ARGS = "That setting needs two values; unset with the setting name and the first argument. "
ERR_SET_URLPATTERN_SPECIFIC_VARS = "You need to include all of the following variables in your pattern: `{environment}`, `{urlseparator}`, `{basedomain}`"
ERR_SETUP_PARAM_MISSING = "You need to tell me which repo. Try `%s setup username/reponame`" % COMMAND
ERR_SETUP_PARAM_FORMAT = ("The repo name should be two parts; the GitHub username and the actual"
                          " repository name. e.g. the React library's repo would be `facebook/react`")
ERR_SETUP_CHANNEL_REPO_EXISTS = "It looks as though that repo is already setup in this channel"
ERR_SETUP_REPO_EXISTS = "That repo is already setup in a different channel. Only one channel per repo."
ERR_SETUP_CHANNEL_EXISTS = "This channel is already setup for a different repo. Only one repo per channel."
ERR_RESET_FAILURE = "No config found for this channel"
ERR_USER_BUTTON_FALLBACK = "You are unable to introduce yourself for some reason. Sorry."
ERR_GOODBYE_NO_USER = "Nothing to forget; I couldn't find you in the DB."
ERR_DEPLOY_ARGS = "You must specify what and where to deploy, as `deploy <branch-or-tag> to <environment>`"
ERR_DEPLOY_VALID_ENV = "I don't recognise that environment name"
ERR_DEPLOY_REFENV_VALIDATION = "That environment doesn't get built from that ref according to the supported workflow. "
ERR_DEPLOY_REMOTE = "Something went wrong: "

SLACK_SIGNING_SECRET_VERSION = "v0"

dynamodb = boto3.resource('dynamodb', region_name=os.environ['SLS_AWS_REGION'])
lambda_client = boto3.client(
    'lambda', region_name=os.environ['SLS_AWS_REGION'])

logger = logging.getLogger()
if logger.handlers:
    for handler in logger.handlers:
        logger.removeHandler(handler)
logging.basicConfig(level=logging.INFO)
logger.setLevel(logging.INFO)

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


def set(text, context):
    """
    Allows individual settings to be created
    """
    if len(text) == 0 or text.strip() == '':
        return slack_response(FN_RESPONSE_SET)

    parts, setting = validate_input(text, FN_RESPONSE_SET)

    if setting == 'url':
        if len(parts) != 3:
            return slack_response(ERR_SET_SETTING_3_ARGS + FN_RESPONSE_SET)
        value = {
            parts[1]: parts[2]
        }
        val_type = "M"

    if setting == 'urlpattern':
        if len(parts) != 2:
            return slack_response(ERR_SET_SETTING_2_ARGS + FN_RESPONSE_SET)
        value = parts[1]
        if ('{environment}' not in value and
            '{urlseparator}' not in value and
                '{basedomain}' not in value):
            return slack_response(ERR_SET_URLPATTERN_SPECIFIC_VARS)
        val_type = "S"

    if setting == 'basedomain':
        if len(parts) != 2:
            return slack_response(ERR_SET_SETTING_2_ARGS + FN_RESPONSE_SET)
        value = parts[1]
        val_type = "S"

    if setting == 'urlseparator':
        if len(parts) != 2:
            return slack_response(ERR_SET_SETTING_2_ARGS + FN_RESPONSE_SET)
        value = parts[1]
        val_type = "S"

    setting = 'setting_{}'.format(setting)

    table = dynamodb.Table(os.environ['DYNAMODB_TABLE_PROJECT'])
    entries = table.scan()
    for entry in entries['Items']:
        if entry['slack_channelid'] == context['channel_id']:
            entry['updatedAt'] = int(time.mktime(datetime.now().timetuple()))
            if setting in entry and val_type == "M":
                # only override the key we've changed
                value = entry[setting]
                value[parts[1]] = parts[2]

            table.update_item(
                Key={
                    'repository': entry['repository'],
                    'slack_channelid': entry['slack_channelid']
                },
                UpdateExpression='SET {} = :v'.format(setting),
                ExpressionAttributeValues={
                    ':v': value,  # surely {val_type: value} for maps ?
                },
                ReturnValues="ALL_NEW"
            )
            return slack_response(FN_RESPONSE_SET_CONFIRM % (setting[8:], " ".join(parts[1::])))

    return slack_response(ERR_SET)


def unset(text, context):
    """
    Allows individual settings to be deleted
    """
    if text is None or len(text) == 0:
        return slack_response(FN_RESPONSE_UNSET)

    parts, setting = validate_input(text, FN_RESPONSE_UNSET)

    if setting == 'url':
        if len(parts) != 2:
            return slack_response(ERR_SET_SETTING_3_ARGS + FN_RESPONSE_UNSET)
        val_type = "M"

    if setting == 'urlpattern':
        if len(parts) != 1:
            return slack_response(ERR_SET_SETTING_2_ARGS + FN_RESPONSE_UNSET)
        val_type = "S"

    if setting == 'urlseparator':
        if len(parts) != 1:
            return slack_response(ERR_SET_SETTING_2_ARGS + FN_RESPONSE_UNSET)
        val_type = "S"

    if setting == 'basedomain':
        if len(parts) != 1:
            return slack_response(ERR_SET_SETTING_2_ARGS + FN_RESPONSE_UNSET)
        val_type = "S"

    setting = 'setting_{}'.format(setting)

    table = dynamodb.Table(os.environ['DYNAMODB_TABLE_PROJECT'])
    entries = table.scan()
    for entry in entries['Items']:
        if entry['slack_channelid'] == context['channel_id']:
            entry['updatedAt'] = int(time.mktime(datetime.now().timetuple()))

            expr = "REMOVE {}".format(setting)
            attrs = None
            if setting in entry and val_type == "M":
                # only remove the key we've changed
                value = entry[setting]
                value.pop(parts[1])
                expr = 'SET {} = :v'.format(setting)
                attrs = {
                    ':v': {val_type: value},
                }

            table.update_item(
                Key={
                    'repository': entry['repository'],
                    'slack_channelid': entry['slack_channelid']
                },
                UpdateExpression=expr,
                ExpressionAttributeValues=attrs,
                ReturnValues="ALL_NEW"
            )
            return slack_response(FN_RESPONSE_SET_CONFIRM % (setting[8:], " ".join(parts[1::])))

    return slack_response(FN_RESPONSE_UNSET)


def get(text, context):
    """
    Prints out current setup information
    """
    table = dynamodb.Table(os.environ['DYNAMODB_TABLE_PROJECT'])
    entries = table.scan()
    for entry in entries['Items']:
        if entry['slack_channelid'] == context['channel_id']:
            if 'setting_baseurl' in entry and 'setting_basedomain' not in entry: # for backward compatibility
                entry['setting_basedomain'] = entry['setting_baseurl']
            if 'setting_basedomain' not in entry:
                entry['setting_basedomain'] = "--NOT SET--"
            if 'setting_url' not in entry:
                entry['setting_url'] = "--NOT SET--"
            if 'setting_url_pattern' in entry and 'setting_urlpattern' not in entry: # for backward compatibility
                entry['setting_urlpattern'] = entry['setting_url_pattern']
            if 'setting_urlpattern' not in entry:
                entry['setting_urlpattern'] = 'https://{environment}{urlseparator}{basedomain}/'
            if 'setting_url_separator' in entry and 'setting_urlseparator' not in entry: # for backward compatibility
                entry['setting_urlseparator'] = entry['setting_url_separator']
            if 'setting_urlseparator' not in entry:
                entry['setting_urlseparator'] = '.'
            return slack_response(
                FN_RESPONSE_GET_EXISTS % (
                    entry['repository'],
                    entry['setting_basedomain'],
                    entry['setting_url'],
                    entry['setting_urlpattern'],
                    entry['setting_urlseparator']
                )
            )

    return connect_github_user(FN_RESPONSE_GET_NOTEXISTS, entry['repository'], entry['slack_channelid'], FN_RESPONSE_GET_ALL_GH_KNOWN)


def setup(repo=None, context=None):
    """
    Initialise project
    """
    logging.info("context = {%s}" % ', '.join("%s: %r" %
                                              (key, val) for (key, val) in context.items()))
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
    logging.info("item = {%s}" % ', '.join("%s: %r" % (key, val)
                                           for (key, val) in item.items()))

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
            return connect_github_user(FN_RESPONSE_HELLO, entry['repository'], entry['slack_channelid'], FN_RESPONSE_HELLO_NO_UNKNOWNS)


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


def deploy(text, context):
    """
    Manually triggers a deployment to a specific environment
    """
    parts = text.split()
    if len(parts) != 3:
        return slack_response(ERR_DEPLOY_ARGS)

    ref = parts[0].lower()
    env = parts[2].lower()

    if env not in ('preview', 'test', 'staging', 'production'):
        # no force-building PRs
        return slack_response(ERR_DEPLOY_VALID_ENV)

    if (env == 'production' and ref[0:1] != 'v'):
        return slack_response(ERR_DEPLOY_REFENV_VALIDATION)

    if ref[0:4] != 'refs':
        if env == 'production':
            ref = "refs/tags/{}".format(ref)
        else:
            ref = "refs/heads/{}".format(ref)

    logging.info('Manually deploying {} to {}'.format(ref, env))

    # get the required bits: commit_sha, repo
    table = dynamodb.Table(os.environ['DYNAMODB_TABLE_PROJECT'])
    entries = table.scan()
    for entry in entries['Items']:
        if entry['slack_channelid'] == context['channel_id']:
            repository = entry['repository']
            break

    payload = {
        'repository': repository,
        'environment': env,
        'ref': ref,
        'description': 'Manually triggered from Slack via SN Deploybot with command `{}`'.format(text),
        'trigger': 'slack_command',
    }
    response = lambda_client.invoke(
        FunctionName="{}-github_deployment_create".format(
            os.environ['FUNCTION_PREFIX']),
        InvocationType='Event',
        Payload=json.dumps(payload)
    )
    return slack_response(FN_RESPONSE_DEPLOY % (ref, env), True)

    # since changing invoke from RequestResponse to Event (async call) we no longer get a useful return
    # string_response = response["Payload"].read().decode('utf-8')
    # parsed_response = json.loads(string_response)
    # if 'errorType' in parsed_response:
    #     return slack_response("{} `{}`".format(ERR_DEPLOY_REMOTE, parsed_response['errorMessage']))

    # logging.info(parsed_response)
    # return parsed_response


#
#
# Shared Slack functionality
#
#


def connect_github_user(message, repository, slack_channelid, message_fallback=None):
    response = lambda_client.invoke(
        FunctionName="{}-github_collaborators".format(
            os.environ['FUNCTION_PREFIX']),
        InvocationType='RequestResponse',
        Payload=json.dumps({'repository': repository})
    )

    string_response = response["Payload"].read().decode('utf-8')
    parsed_response = json.loads(string_response)

    table = dynamodb.Table(os.environ['DYNAMODB_TABLE_USER'])
    entries = table.scan()
    gh_users = [x['github_username'] for x in entries['Items']]
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
        "response_type": response_type,
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
        bytes(os.environ['SLACK_SIGNING_SECRET'], 'utf-8'),
        bytes(basestring, 'utf-8'),
        hashlib.sha256
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
    logging.info(d)

    data = {}
    for key, value in d.items():
        # logging.info('got data "%s"="%s"'%(key, value))
        data[key] = get_form_variable_value(value)

    if data['command'] not in [COMMAND, '/deploy']:
        logging.error("Unexpected command")
        return response({"message": "Unexpected command"}, 500)

    if 'text' not in data or data['text'] == "":
        logging.warn("No text in command")
        data['text'] = 'help'
        data['command'] = COMMAND

    context = {
        "channel_id": data['channel_id'],
        "channel_name": data['channel_name'],
        "user_id": data['user_id'],
        "user_name": data['user_name'],
        "response_url": data['response_url'],
        "trigger_id": data['trigger_id'],
    }

    if data['command'] == COMMAND:
        return call_function(data['text'], context)
    else:
        return call_function("{} {}".format(data['command'][1:], data['text']), context)


def response(body, status=200):
    """
    Builds the data structure for an AWS Lambda reply
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


def validate_input(text, command_response):
    """
    Validates user input and formats it for processing
    """
    parts = text.split()
    setting = format_input(parts[0].lower())

    if setting not in SET_OPTIONS.values():
        return slack_response(ERR_SET_SETTING_NOT_RECOGNISED + command_response)

    return (parts, setting)


def format_input(setting):
    """
    Formats valid input setting to db keyword
    """
    return SET_OPTIONS.get(setting, None)


def get_form_variable_value(form_var):
    """
    Cleans up submitted form vars on the assumption they are single values
    """
    return form_var[0]


if __name__ == "__main__":
    receive({
        'body': 'command={}&text=help&channel_id=abc123&channel_name=test&user_id=def456&user_name=isaac&response_url=hi&trigger_id=1'.format(
            os.environ['COMMAND']),
        'headers': {
            'X-Slack-Request-Timestamp': '4e3287efe5ff45cb3976a661e63313bf75bdb84e88b5d201f85f6bf95eee7e5e', 'X-Slack-Request-Timestamp': '1546466712', 'X-Slack-Signature': '4922ca26f7d1138af6541a936ed0c8ca=8701594fd420b5f2ae8ada64a505a0dd728ec6a046a45d506cd4703be637b6f9'}}, '')
