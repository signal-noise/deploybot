# CircleCI project requirements

Right now [CircleCI](https://circleci.com) is the CI platform we use, but this
project will make it easier to switch between them, as the workflow logic will
be abstracted away.

CircleCI doesn't have a very good API unfortunately, so there are a few
requirements placed on the CircleCI project configuration, found in the repo's
`.circleci/circleyml` file.

This repo's own
[config file](https://github.com/signal-noise/deploybot/tree/master/.circleci/config.yml)
follows the recommendations so can be used as an example.

Firstly, the config shouldn't automatically trigger any builds on its own; leave
the triggering to deploybot.

Secondly, a `job` must exist called `build` (the API call we use will only
trigger a job of that name for some reason); this job needs to do everything
required to exexcute a deployment.

Note that this job will be provided with several ENV vars when it is triggered:

- \$ENVIRONMENT (name of the environment)
- \$VERSION (name of the version; might be semver compatible or a truncated
  commit SHA)
- \$SUBDOMAIN (for environments without a full URL of their own, like PR builds,
  this gives the required first part of the domain)
- \$URL (the full expected URL of the final deployment)

There also needs to be a root level `notify` clause in the YAML file, configured
to post a webhook payload to your installation's `circleci_event` function
endpoint.
