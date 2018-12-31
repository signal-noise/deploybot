# deploybot

> Service with Slack bot interface, connecting CircleCI to GitHub

This project exists in order to allow easy workflow support between Slack, GitHub and CircleCI. It is built using the Serverless framework for AWS Lambda, using Python 3.7.

We wrote this to help us with our own current setup; to fill gaps in the tooling we currently use. It's in a very early stage and needs a lot of work to be really stable.

This is an introduction; please also read the detailed [documentation](./docs).

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

The default command is configurable but defaults to `cimon`.

In a slack channel, typing `/cimon setup <username>/<repository>` will start the process off, and trigger a message asking you to select your GitHub username from the list of users with access to that repository. `/cimon reset` will forget the setup, though not the user connections.

`/cimon hello` will get the bot to look at the channel's existing repository for GH users that it doesn't already know the Slack usernames of and return a set of buttons; pressing one will claim that GH username for the user who pressed it. `/cimon goodbye` undoes this for your user.

`/cimon config` will output the current configuration in place.

`/cimon deploy <environment>` triggers a deployment

`/cimon list` shows deployments

## Installation

Please read the [Installation guide](./docs/installation.md) in the documentation.

## Contributing

Please read about [submitting contributions](./docs/CONTRIBUTING.md).
