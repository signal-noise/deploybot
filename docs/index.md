# Deploybot documentation

This project exists in order to allow easy workflow support between Slack,
GitHub and CircleCI. It is built using the Serverless framework for AWS Lambda,
using Python 3.7.

## Functionality

In essence, the app subscribes to GitHub events, which it uses to trigger GitHub
deployments at moments that support the given workflow. The Deployment events
then trigger jobs to run on CircleCI with all status information returning to
GitHub.

Each Slack channel it is configured on will relate to a single GitHub
repository. All GitHub events relating to the workflow are posted to Slack
intelligently, with updates to existing messages and message interactivity where
appropriate, and of course with the relevant users @ mentioned.

Triggers can also be manually activated via the Slack channel; anyone on the
channel has permission to run any command.

### Supported workflows

As this project is in very early days, the workflow is pretty hardcoded right
now. For details please check out the
[workflow documentation](./project_workflow.md).

## Usage

The default command is configurable but defaults to `cimon`.

In a slack channel, typing `/cimon setup <username>/<repository>` will start the
process off, and trigger a message asking you to select your GitHub username
from the list of users with access to that repository. `/cimon reset` will
forget the setup, though not the user connections.

`/cimon hello` will get the bot to look at the channel's existing repository for
GH users that it doesn't already know the Slack usernames of and return a set of
buttons; pressing one will claim that GH username for the user who pressed it.
`/cimon goodbye` undoes this for your user.

`/cimon config` will output the current configuration in place.

`/cimon deploy <environment>` triggers a deployment

`/cimon list` shows deployments

## Installation

Please read the [Installation guide](./docs/installation.md) in the
documentation.

## Contributing

Please read about [submitting contributions](./docs/CONTRIBUTING.md).

## Project structure

The project is a single service (inasmuch as there is a single serverless config
file), but with various endpoints and subareas.

The three main divisions of the codebase are around the third party connectors:
`slack`, `github` and `circleci`. Each of these has a single file per endpoint.

Some of the endpoints have HTTP access enabled in order to connect to e.g.
webhook events; these are all secured with tokenised validation according to
each of the providers' specs.

Other endpoints are only accessible via internal Lambda invoke calls, and are
unsecured other than inbuilt AWS permissions.

You may also want to read about the [data models](./data_models.md).

### Slack

Slack functionality is divided in the same way that Slack's own connectors are
split. ; we have an endpoint for each of `message`, `command`, `interactive` and
`event`.

- `command` is the guts of the bot; this handles all commands sent to the main
  slash command exposed by the Slack app config.
- `interactive` is the endpoint that handles responses triggered by buttons
  pressed in custom messages.
- `message` is used to send event-based messages to a slack channel based on
  external stimuli
- `event` is the endpoint for Slack events such as users joining rooms.

Read the [detailed description](./functionality_slack.md).

### Github

The GitHub connectors are slightly more varied.

- `webhook` receives all events from a repository and therefore has an HTTP
  endpoint.
- `collaborators` takes a repository as input, queries the GH GraphQL API and
  returns just the usernames of the people with access to that repo. This is not
  configured for HTTP access, and is only meant to be called by other Lambda
  functions.
- `deployment` creates and updated GH Deployments and keeps the relevant
  DynamoDB table in sync. It is only meant to be called by other Lambda
  functions.

Read the [detailed description](./functionality_github.md).

### CircleCI

- `trigger` POSTS to the CircleCI API to trigger a job called `build` on the
  given repo.
- `webhook` receives all events from a repository via the `notify` clause in the
  circleci config file; it therefore has an HTTP endpoint.

Read the [detailed description](./functionality_circleci.md).
