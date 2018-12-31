# deploybot

> Service with Slack bot interface, connecting CircleCI to GitHub

This project exists in order to allow easy workflow support between Slack, GitHub and CircleCI. It is built using the Serverless framework for AWS Lambda, using Python 2.7.

## Functionality

In essence, the app subscribes to GitHub events, which it uses to trigger GitHub deployments at moments that support the given workflow. The Deployment events then trigger jobs to run on CircleCI with all status information returning to GitHub.

Each Slack channel it is configured on will relate to a single GitHub repository. All GitHub events relating to the workflow are posted to Slack intelligently, with updates to existing messages and message interactivity where appropriate, and of course with the relevant users @ mentioned.

Triggers can also be manually activated via the Slack channel; anyone on the channel has permission to run any command.

### Supported workflows

As this project is in very early days, the workflow is pretty hardcoded right now. It's based on [GitHub Flow](https://guides.github.com/introduction/flow/), with a couple of extra items; this is all the moments a deployment is triggered:

- As soon as a PR is created the `headRef` of that PR is built, and the build is linked in a comment on the PR
- Each subsequent push to a branch with an open PR triggers a rebuild of that `PR` environment
- Each push to `master` (usually a merge from a PR) triggers a build of the `Preview` environment
- Each push to any branch with a name starting with `release` (e.g. `release/v1.3`) triggers a build to the `test` environment
- Manual triggers from Slack can trigger builds to `staging` of anything that's already been built to `test`
- Pushing tags with names starting with a `v` (e.g. `v1.3`) will trigger a build to the `production` environment

## Usage

The default command is called `cimon`.

In a slack channel, typing `/cimon setup <username>/<repository>` will start the process off, and trigger a message asking you to select your GitHub username from the list of users with access to that repository. `/cimon reset` will forget the setup, though not the user connections.

`/cimon hello` will get the bot to look at the channel's existing repository for GH users that it doesn't already know the Slack usernames of and return a set of buttons; pressing one will claim that GH username for the user who pressed it. `/cimon goodbye` undoes this for your user.

`/cimon config` will output the current configuration in place.

`/cimon deploy <environment>` triggers a deployment

`/cimon list` shows deployments

## Installation

Set up an AWS account, following the [Serverless documentation](https://serverless.com/framework/docs/providers/aws/guide/credentials/). Get the Access Key and Secret, and save them to your `~.aws/credentials` file under the `deploybot` profile if you intend to deploy manually (recommended). Use the separate [CloudFormation template](./dynamoDB_cf.template) file to install the DynamoDB tables (note that the tablenames are all generated as though `service` is `deploybot` and `stage` is `prod`). Run a serverless deployment so you have the endpoints you'll need when setting up other services.

Set up a GitHub app for your organisation; navigate to your organisation settings, go to GitHub Apps and create a new one. Fill in the Name, Description and Homepage fields, then add the endpoint for your `github_event` function to the Webhook URL field. You then need to install it; ideally to all repositories. You'll need to get the App's `ID` and `Private Key` as well as its `Installation ID`.

Set up a [Slack app](https://api.slack.com/apps/) and enable `Incoming Webhooks`, `Interactive Components` (add the `slack_interactive` endpoint here) and `Slash Commands` (the `slack_command` endpoint goes in here). You'll need the Slack App Signing Secret, Webhook URL, and Team ID.

Log in to your CircleCI accoutn and generate a personal API token.

---

configure circleci project for auto-deploy - see other readme

`npm i`

optionally install docker...(nb circleci)

sls deploy

## Project structure

The project is a single service (inasmuch as there is a single serverless config file), but with various endpoints and subareas.

The three main divisions of the codebase are around the third party connectors: `slack`, `github` and `circleci`. Each of these has a single file per endpoint.

Some of the endpoints have HTTP access enabled in order to connect to e.g. webhook events; these are all secured with tokenised validation according to each of the providers' specs.

Other endpoints are only accessible via internal Lambda invoke calls, and are unsecured other than inbuilt AWS permissions.

### Slack

Slack functionality is divided in the same way that Slack's own connetors are split. ; we have an endpoint for each of `message`, `command`, `interactive` and `event`.

- `command` is the guts of the bot; this handles all commands sent to the main slash command exposed by the Slack app config.
- `interactive` is the endpoint that handles responses triggered by buttons pressed in custom messages.
- `message` is used to send event-based messages to a slack channel based on external stimuli
- `event` is the endpoint for Slack events such as users joining rooms.

### Github

The GitHub connectors are slightly more varied.

- `webhook` receives all events from a repository and therefore has an HTTP endpoint.
- `collaborators` takes a repository as input, queries the GH GraphQL API and returns just the usernames of the people with access to that repo. This is not configured for HTTP access, and is only meant to be called by other Lambda functions.
- `deployment` creates and updated GH Deployments and keeps the relevant DynamoDB table in sync. It is only meant to be called by other Lambda functions.

### CircleCI

- `trigger` POSTS to the CircleCI API to trigger a job called `build` on the given repo.

### Asana

...

## Data model

Data is saved into three `DynamoDB` tables as follows.

### Project

This saves the `slack_channelid` against the `repository` (in the format `github-username/repository-name`) to act as a reference and enforce a single channel against a single repo. It also saves the `slack_channel` (i.e. the human-readable name) to simplify things and help debugging.

### User

This simple table saves the `slack_userid` against the `github_username`, to allow _@_ notifications from GitHub events in Slack. Again, it also stores `slack_username` for ease of use.

### Deployment

The core of the app revolves around this. Each GitHub `deployment` corresponds to a single item in this table. Each item in this table can have all the following attributes:

- `repository`
- `id` (GH deployment ID)
- `ref`
- `commit_author_github_login`
- `commit_sha`
- `trigger`
- `pr` (PR number)
- `environment`
- Build number
- Build URL
- Deploy URL
- Deploy datetime
- Slack Message ID
- Ticket reference (Asana or gh ticket)
