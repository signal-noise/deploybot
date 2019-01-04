# Project setup

This document is about setting up deploybot to work on a spcific project /
repository, once you have completed [installation](./installation.md).

Setup should be easy and hopefully intuitive. Right now the workflow is also
hard coded so you'll get deployments triggered at all
[the moments](./project_workflow.md) _we_ think you should. This will change.

## Before you begin

Make sure deploybot is fully [installed](./installation.md) according to the
docs, including the hosting on AWS Lambda, the Slack app and GitHub app and all
tokens and ENV vars.

## GitHub requirements

At the moment deploybot expects you to already have a repository created, and
you'll be better off if the right people already have write permissions.

Please add a CircleCI configuration file to the repo and make sure it follows
[this guide](./circleci_project_requirements.md). You may as well set up the
CircleCI interface and trigger a build at this point so CircleCI is good to go.

Now CircleCI is set up you can go ahead and set up protected branch rules to
include required statuses; this is handled by deploybot.

## Slack Config

Go to the Slack channel you want to use for the dev side of this. Note that
_anyone on this channel will be able to trigger deployments_, so you may want it
to be private.

Setup the channel as deploybot's interface for your repo with
`/<your-command> setup repouser/reponame`, and then
`/<your-command> set baseurl devdomain.com`, perhaps followed by
`/<your-command> set url production properdomain.com` and any other setup you'd
like to do.

Encourage team members to all type `/<your-command> hello` for the smart
notifications. Until they come in to play however you're also recommended to add
the Github app to the channel and subscribe to notifications.
