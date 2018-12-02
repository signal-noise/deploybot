# deploybot

> Service with Slack bot interface, connecting CircleCI to GitHub

This project exists in order to allow easy workflow support between Slack, GitHub and CircleCI. It is built using the Serverless framework for AWS Lambda, using Python 2.7.

## Functionality

### Supported workflows

## Usage

## Installation

## Project structure

The project is a single service (inasmuch as there is a single serverless config file), but with various endpoints and subareas.

The three main divisions of the codebase are around the third party connectors: `slack`, `github` and `circleci`. Each of these has a single file per endpoint.

### Slack

Slack functionality is divided in the same way that Slack's own connetors are split; we have an endpoint for each of `message`, `command`, `interactive` and `event`.

## Data model

Project, User, Build
