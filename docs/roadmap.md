# Deploybot roadmap

This is a very high level view of where we hope the project will go, in a very
approximate order.

If you'd like to suggest anything please open an issue; if you'd like to help
please [submit a PR](./CONTRIBUTING.md)!

- [x] Get GitHub deployments created for all events in our own workflow where
      builds ought to happen
- [x] Trigger a build for each GitHub Deployment
- [x] Manually trigger deployments for specific environments from Slack
- [ ] Create smarter Slack notifications than the GitHub or CircleCI apps can
      alone (see issue
      [#36](https://github.com/signal-noise/deploybot/issues/36))
- [ ] Make the workflow configurable project-by-project and as a general
      default. This should affect which environments exist, what gets deployed
      to which and when.
- [ ] Add issue handling into the smart messaging
- [ ] Add a plugin architecture for both CI systems and Issue trackers, allowing
      other systems to be added more easily
