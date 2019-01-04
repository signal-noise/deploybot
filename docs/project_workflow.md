### Supported workflows

As this project is in very early days, the workflow is pretty hardcoded right
now. It's based on [GitHub Flow](https://guides.github.com/introduction/flow/),
with a couple of extra items; this is all the moments a deployment is triggered:

- As soon as a PR is created the `headRef` of that PR is built, and the build is
  linked in a comment on the PR
- Each subsequent push to a branch with an open PR triggers a rebuild of that
  `PR` environment
- Each push to `master` (usually a merge from a PR) triggers a build of the
  `Preview` environment
- Each push to any branch with a name starting with `release` (e.g.
  `release/v1.3`) triggers a build to the `test` environment
- Manual triggers from Slack can trigger builds to `staging` of anything that's
  already been built to `test`
- Pushing tags with names starting with a `v` (e.g. `v1.3`) will trigger a build
  to the `production` environment
