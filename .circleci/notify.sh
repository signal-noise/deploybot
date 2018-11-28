#!/bin/bash
# sends a notification to Slack using the Webhook API, or to GitHub if it's a PR build

  # post to Slack
  TEXT="New version has just been deployed by <${CIRCLE_BUILD_URL}|CircleCI>."

  curl -X POST --data-urlencode "payload={\"text\":\"${TEXT}\",\"channel\":\"${SLACK_CHANNEL}\"}" ${SLACK_WEBHOOK_URL}

  echo "Posted \"${TEXT}\""