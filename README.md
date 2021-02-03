# deploybot
<!-- ALL-CONTRIBUTORS-BADGE:START - Do not remove or modify this section -->
[![All Contributors](https://img.shields.io/badge/all_contributors-1-orange.svg?style=flat-square)](#contributors-)
<!-- ALL-CONTRIBUTORS-BADGE:END -->

> Automate deployments at all the right times, and manually from Slack

This project exists in order to allow easy workflow support between Slack,
GitHub and CircleCI. It is built using the Serverless framework for AWS Lambda,
using Python 3.7.

We wrote this to help us with our own current setup; to fill gaps in the tooling
we currently use. It's in a very early stage and needs a lot of work to be
really stable. If you'd like to help out, [please do](./docs/CONTRIBUTING.md)!

This is an introduction; please also read the detailed [documentation](./docs).

## Functionality

In essence, the app subscribes to GitHub events, which it uses to trigger GitHub
deployments at moments that support the
[given workflow](./docs/project_workflow.md). The Deployment events then trigger
jobs to run on CircleCI with all status information returning to GitHub.

Each Slack channel it is configured on will relate to a single GitHub
repository. All GitHub events relating to the workflow are posted to Slack
intelligently, with updates to existing messages and message interactivity where
appropriate, and of course with the relevant users @ mentioned.

Triggers can also be manually activated via the Slack channel; anyone on the
channel has permission to run any command.

## Usage

The default command is configurable but defaults to `cimon`.

In a slack channel, typing `/cimon setup <username>/<repository>` will start the
process off, and trigger a message asking you to select your GitHub username
from the list of users with access to that repository. `/cimon reset` will
forget the setup, though not the user connections.

`cimon set xxx yyy` allows settings to be set up; at the moment a `basedomain` and
`url`s for any environments that don't rely on subdomains of the `basedomain` should
be setup; a `urlpattern` can also be added to change the autogenerated URL
structure.

`/cimon hello` will get the bot to look at the channel's existing repository for
GH users that it doesn't already know the Slack usernames of and return a set of
buttons; pressing one will claim that GH username for the user who pressed it.
`/cimon goodbye` undoes this for your user.

`/cimon get` will output the current configuration in place.

`/cimon deploy <environment>` triggers a deployment

`/cimon list` shows deployments

### Supported workflows

As this project is in very early days, the workflow is pretty hardcoded right
now. It's based on [GitHub Flow](https://guides.github.com/introduction/flow/),
with a couple of extra items; please
[read more here](./docs/project_workflow.md).

## Installation

Please read the [Installation guide](./docs/installation.md) in the
documentation.

## Contributing

Please read about [submitting contributions](./docs/CONTRIBUTING.md).

## Contributors ✨

Thanks goes to these wonderful people ([emoji key](https://allcontributors.org/docs/en/emoji-key)):

<!-- ALL-CONTRIBUTORS-LIST:START - Do not remove or modify this section -->
<!-- prettier-ignore-start -->
<!-- markdownlint-disable -->
<table>
  <tr>
    <td align="center"><a href="https://github.com/nattog"><img src="https://avatars.githubusercontent.com/u/38443772?v=4?s=100" width="100px;" alt=""/><br /><sub><b>Guy Purssell</b></sub></a><br /><a href="https://github.com/signal-noise/deploybot/commits?author=nattog" title="Code">💻</a></td>
  </tr>
</table>

<!-- markdownlint-restore -->
<!-- prettier-ignore-end -->

<!-- ALL-CONTRIBUTORS-LIST:END -->

This project follows the [all-contributors](https://github.com/all-contributors/all-contributors) specification. Contributions of any kind welcome!