# How to contribute

I'm really happy that you're interested in helping out with this project; I've
been thinking about it for a long time and having spent a few weeks on it now I
can see it just getting bigger and bigger; any and all help is much appreciated.

As this is very early days for the project there's not a lot in the way of
resources, but please check out the [documentation](./index.md) including the
[roadmap](./roadmap.md), and also the
[list of issues](https://github.com/signal-noise/deploybot/issues).

Please submit an issue if you need help with anything. If this takes off we'll
put more resources in place for support.

We have a [code of conduct](./CODE_OF_CONDUCT.md) so please make sure you follow
it.

## Testing

We haven't yet put anything in place for testing - not even a harness. CI
deployment is (ironically) also broken at the moment. If you'd like to help with
this please submit a PR!

## Submitting changes

Please send a
[GitHub Pull Request to deploybot](https://github.com/signal-noise/deploybot/pull/new/master)
with a clear list of what you've done (read more about
[pull requests](http://help.github.com/pull-requests/)). When you send a pull
request, please make sure you've covered off all the points in the template.

Please follow [PEP-8](https://www.python.org/dev/peps/pep-0008/) and make sure
you've read about our workflow (below); in essence make sure each Pull Request
is atomic but don't worry too much about the commits themselves as we use
squash-and-merge.

Note that if you alter the Python required packages you'll need to run
`npm run build` which will repopulate `vendored`, for which you'll need docker
running locally. We commit this folder into the repo to allow CI to build easily
without doing complex docker-in-docker tricks.

## Our workflow

We use [GitHub flow](https://guides.github.com/introduction/flow/); it's a lot
like git-flow but simpler and more forgiving. Some additional pieces we've put
in place are:

- We use the `squash and merge` strategy to merge Pull Requests.
- QA is built from branches starting with `release`, e.g. `release/v0.1`. Only
  hotfixes should be committed to those branches.
- Production is built from tags starting with a `v`, e.g. `v0.1`. The tags
  should be created from a release branch

In effect this means:

- Don't worry about individual commits. They will be preserved, but not on the
  main `master` branch history, so feel free to commit early and often, using
  git as a save mechanism.
- Your Pull Request title and description become very important; they are the
  history of the master branch and explain all the changes.
- You ought to be able to find any previous version easily using GitHub tabs, or
  [Releases](https://github.com/signal-noise/deploybot/releases)

Thanks, Marcel Kornblum
