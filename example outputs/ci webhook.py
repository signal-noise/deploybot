{
    u'payload': {
        u'username': u'signal-noise',
        u'compare': None,
        u'platform': u'2.0',
        u'vcs_url': u'https://github.com/signal-noise/deploybot',
        u'ssh_disabled': True,
        u'oss': False,
        u'build_url': u'https://circleci.com/gh/signal-noise/deploybot/171',
        u'committer_date': u'2018-12-27T00:54:08Z',
        u'author_name': u'marcelkornblum',
        u'build_num': 171,
        u'canceled': False,
        u'reponame': u'deploybot',
        u'retry_of': None,
        u'pull_requests': [
            {
                u'url': u'https://github.com/signal-noise/deploybot/pull/32',
                u'head_sha': u'0eccfce94f07d2f545ee558da06b7c94cf564213'
            }
        ],
        u'vcs_revision': u'0eccfce94f07d2f545ee558da06b7c94cf564213',
        u'vcs_tag': None,
        u'previous': {
            u'build_num': 169,
            u'status': u'success',
            u'build_time_millis': 1606
        },
        u'build_time_millis': 9406,
        u'committer_email': u'email@gmail.com',
        u'context_ids': [
            u'sn-global'
        ],
        u'author_email': u'email@gmail.com',
        u'picard': {
            u'build_agent': {
                u'image': u'circleci/picard:0.1.1250-22bf9f5d',
                u'properties': {
                    u'build_agent': u'0.1.1250-22bf9f5d',
                    u'executor': u'docker'}
            },
            u'executor': u'docker',
            u'resource_class': {
                u'ram': 4096,
                u'cpu': 2.0,
                u'class': u'medium'
            }
        },
        u'no_dependency_cache': False,
        u'is_first_green_build': False,
        u'all_commit_details_truncated': False,
        u'failed': False,
        u'previous_successful_build': {
            u'build_num': 169,
            u'status': u'success',
            u'build_time_millis': 1606
        },
        u'stop_time': u'2018-12-27T00:54:25.114Z',
        u'branch': u'trigger-circleci',
        u'build_parameters': {
            u'CIRCLE_JOB': u'test'
        },
        u'queued_at': u'2018-12-27T00:54:14.045Z',
        u'has_artifacts': True,
        u'body': u'',
        u'canceler': None,
        u'lifecycle': u'finished',
        u'start_time': u'2018-12-27T00:54:15.708Z',
        u'timedout': False,
        u'subject': u'endpoint for circleci notifications',
        u'ssh_users': [],
        u'usage_queued_at': u'2018-12-27T00:54:14.023Z',
        u'user': {
            u'is_user': True,
            u'name': u'Marcel Kornblum',
            u'avatar_url': u'https://avatars1.githubusercontent.com/u/1162347?v=4',
            u'login': u'marcelkornblum',
            u'id': 1162347,
            u'vcs_type': u'github'
        },
        u'dont_build': None,
        u'workflows': {
            u'workspace_id': u'b8cdfe07-4b45-411b-b354-6b14f627e1a0',
            u'workflow_name': u'test_and_build',
            u'upstream_job_ids': [],
            u'workflow_id': u'b8cdfe07-4b45-411b-b354-6b14f627e1a0',
            u'upstream_concurrency_map': {

            },
            u'job_name': u'test',
            u'job_id': u'f03368ed-7fd7-4928-8fad-9c844955eeee'
        },
        u'why': u'github',
        u'vcs_type': u'github',
        u'status': u'success',
        u'retries': None,
        u'owners': [u'marcelkornblum'],
        u'outcome': u'success',
        u'fail_reason': None,
        u'all_commit_details': [{
            u'body': u'',
            u'committer_email': u'email@gmail.com',
            u'commit_url': u'https://github.com/signal-noise/deploybot/commit/0eccfce94f07d2f545ee558da06b7c94cf564213',
            u'author_email': u'email@gmail.com',
            u'author_login': u'marcelkornblum',
            u'committer_date': u'2018-12-27T00:54:08Z',
            u'author_name': u'marcelkornblum',
            u'branch': u'trigger-circleci',
            u'committer_login': u'marcelkornblum',
            u'commit': u'0eccfce94f07d2f545ee558da06b7c94cf564213',
            u'author_date': u'2018-12-27T00:54:08Z',
            u'committer_name': u'marcelkornblum',
            u'subject': u'endpoint for circleci notifications'}],
        u'infrastructure_fail': False,
        u'messages': [],
        u'node': None,
        u'job_name': None,
        u'steps': [
            {
                u'name': u'Spin up Environment',
                u'actions': [
                    {
                        u'status': u'success',
                        u'index': 0,
                        u'timedout': None,
                        u'name': u'Spin up Environment',
                        u'infrastructure_fail': None,
                        u'has_output': True,
                        u'run_time_millis': 9297,
                        u'start_time': u'2018-12-27T00:54:15.745Z',
                        u'truncated': False,
                        u'bash_command': None,
                        u'exit_code': None,
                        u'insignificant': False,
                        u'canceled': None,
                        u'failed': None,
                        u'step': 0,
                        u'continue': None,
                        u'end_time': u'2018-12-27T00:54:25.042Z',
                        u'background': False,
                        u'type': u'test',
                        u'parallel': True,
                        u'allocation_id': u'5c2422b5cba1500008779c3c-0-build/31B6FDC2'
                    }
                ]
            },
            {
                u'name': u'circleci step halt',
                u'actions': [
                    {
                        u'status': u'success',
                        u'index': 0,
                        u'timedout': None,
                        u'name': u'circleci step halt',
                        u'infrastructure_fail': None,
                        u'has_output': False,
                        u'run_time_millis': 23,
                        u'start_time': u'2018-12-27T00:54:25.080Z',
                        u'truncated': False,
                        u'bash_command': u'#!/bin/bash -eo pipefail\ncircleci step halt',
                        u'exit_code': 0,
                        u'insignificant': False,
                        u'canceled': None,
                        u'failed': None,
                        u'step': 101,
                        u'continue': None,
                        u'end_time': u'2018-12-27T00:54:25.103Z',
                        u'background': False,
                        u'type': u'test',
                        u'parallel': True,
                        u'allocation_id': u'5c2422b5cba1500008779c3c-0-build/31B6FDC2'
                    }
                ]
            }
        ],
        u'circle_yml': {
            u'string': u"version: 2\njobs:\n test:\n docker:\n - image: signalnoise/base:10.13\n working_directory: ~/project\n steps:\n - run: circleci step halt\n build:\n docker:\n - image: signalnoise/base:10.13\n steps:\n - run: echo $ENVIRONMENT\n - run: echo $VERSION\n - run: echo $SUBDOMAIN\n old_build:\n docker:\n - image: signalnoise/base:10.13\n steps:\n - checkout\n - run:\n name: Install Dependencies\n command: |\n npm ci\n pip install --upgrade pip\n apk add --no-cache --virtual .build-deps \\\n bzip2-dev \\\n coreutils \\\n dpkg-dev dpkg \\\n findutils \\\n gcc \\\n gdbm-dev \\\n libc-dev \\\n libnsl-dev \\\n libressl-dev \\\n libtirpc-dev \\\n linux-headers \\\n make \\\n ncurses-dev \\\n pax-utils \\\n readline-dev \\\n sqlite-dev \\\n tcl-dev \\\n tk \\\n tk-dev \\\n zlib-dev \\\n python2-dev \\\n libffi-dev\n - run:\n name: Auth keys\n command: |\n ./node_modules/.bin/serverless config credentials \\\n --provider aws \\\n --key $AWS_KEY \\\n --secret $AWS_SECRET\n - run:\n name: Deploy\n command: ./node_modules/.bin/serverless deploy --verbose\n - run:\n name: Notify\n command: echo 'To Do'\nnotify:\n webhooks:\n - url: https://dwlnd1wnmh.execute-api.eu-west-2.amazonaws.com/prod/circleci/webhook\nworkflows:\n version: 2\n test_and_build:\n jobs:\n - test:\n context: sn-global\n"
        },
        u'parallel': 1,
        u'author_date': u'2018-12-27T00:54:08Z',
        u'committer_name': u'marcelkornblum'
    }
}
