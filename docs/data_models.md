## Data model

Data is saved into three `DynamoDB` tables as follows.

### Project

This saves the `slack_channelid` against the `repository` (in the format
`github-username/repository-name`) to act as a reference and enforce a single
channel against a single repo. It also saves the `slack_channel` (i.e. the
human-readable name) to simplify things and help debugging.

### User

This simple table saves the `slack_userid` against the `github_username`, to
allow _@_ notifications from GitHub events in Slack. Again, it also stores
`slack_username` for ease of use.

### Deployment

The core of the app revolves around this. Each GitHub `deployment` corresponds
to a single item in this table. Each item in this table can have all the
following attributes:

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
