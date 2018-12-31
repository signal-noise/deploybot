# Installation

Set up an AWS account, following the [Serverless documentation](https://serverless.com/framework/docs/providers/aws/guide/credentials/). Get the Access Key and Secret, and save them to your `~.aws/credentials` file under the `deploybot` profile if you intend to deploy manually (recommended). Use the separate [CloudFormation template](./dynamoDB_cf.template) file to setup the DynamoDB tables (note that the tablenames are all generated as though `service` is `deploybot` and `stage` is `prod`).

Copy `.env.sample` to `.env` and fill in all the variables as you go. If you want to do local deployments you'll need to `source` this file before doing anything else; if not you'll need to copy all the details to CircleCI environment variables.

You'll need to run a serverless deployment so you have the endpoints you'll need when setting up other services, but it may not work without all the variables; chicken and egg. Give it a go anyway.

Set up a GitHub app for your organisation; navigate to your organisation settings, go to GitHub Apps and create a new one. Fill in the Name, Description and Homepage fields, then add the endpoint for your `github_event` function to the Webhook URL field. Give it the [permissions and subscriptions](./docs/github_app_permissions.md) it will need. You then need to install it; ideally to all repositories. You'll need to get the App's `ID` and `Private Key` as well as its organization [`Installation ID`](https://developer.github.com/v3/apps/#find-repository-installation).

Set up a [Slack app](https://api.slack.com/apps/) and enable `Incoming Webhooks`, `Interactive Components` (add the `slack_interactive` endpoint here) and `Slash Commands` (the `slack_command` endpoint goes in here). You'll need the Slack App Signing Secret, Webhook URL, and Team ID.

Log in to your CircleCI accoutn and generate a personal API token.

---

configure circleci project for auto-deploy - see other readme

`npm i`

optionally install docker...(nb circleci)

sls deploy
