{
    u'username': u'signal-noise', 
    u'compare': None, 
    u'platform': u'2.0', 
    u'vcs_url': u'https://github.com/signal-noise/deploybot', 
    u'ssh_disabled': True, 
    u'oss': False, 
    u'build_url': u'https://circleci.com/gh/signal-noise/deploybot/104', 
    u'committer_date': None, 
    u'author_name': None, 
    u'build_num': 104, 
    u'canceled': False, 
    u'reponame': u'deploybot', 
    u'retry_of': None, 
    u'vcs_revision': u'6366aefd6dfa0891f89417edf88844667e5f2d55', 
    u'vcs_tag': None, 
    u'previous': {
        u'build_num': 102, 
        u'status': u'fixed', 
        u'build_time_millis': 10304
    }, 
    u'build_time_millis': None, 
    u'committer_email': None, 
    u'infrastructure_fail': False, 
    u'author_email': None, 
    u'picard': None, 
    u'no_dependency_cache': False, 
    u'is_first_green_build': False, 
    u'parallel': 1, 
    u'failed': None, 
    u'previous_successful_build': {
        u'build_num': 102, 
        u'status': u'fixed', 
        u'build_time_millis': 10304
    }, 
    u'stop_time': None, 
    u'branch': u'master', 
    u'build_parameters': {
        u'ENVIRONMENT': u'test'
    }, 
    u'job_name': None, 
    u'body': None, 
    u'canceler': None, 
    u'start_time': None, 
    u'timedout': False, 
    u'subject': None, 
    u'ssh_users': [], 
    u'usage_queued_at': u'2018-12-04T21:53:00.807Z', 
    u'user': {
        u'is_user': True, 
        u'name': u'Marcel Kornblum', 
        u'avatar_url': u'https://avatars1.githubusercontent.com/u/1162347?v=4', 
        u'login': u'marcelkornblum', 
        u'id': 1162347, 
        u'vcs_type': u'github'
    }, 
    u'dont_build': None, 
    u'why': u'api', 
    u'vcs_type': u'github', 
    u'retries': None, 
    u'node': None, 
    u'outcome': None, 
    u'fail_reason': None, 
    u'messages': [], 
    u'status': u'not_running', 
    u'circle_yml': {
        u'string': u'version: 2\njobs:\n  test:\n  docker:\n      - image: signalnoise/base:10.13\n# - image: signalnoise/python:10.13-2.7\n    working_directory: ~/project\n    steps:\n      - run: "circleci step halt" # we can\'t deploy from CI at the moment :/\n    - checkout\n      - run:\n          name: Install Dependencies\n          command: |\n            npm ci\n          pip install --upgrade pip\n            apk add --no-cache --virtual .build-deps  \\\n              bzip2-dev \\\n              coreutils \\\n              dpkg-dev dpkg \\\n              findutils \\\n gcc \\\n              gdbm-dev \\\n              libc-dev \\\n              libnsl-dev \\\n              libressl-dev \\\n              libtirpc-dev \\\nlinux-headers \\\n              make \\\n              ncurses-dev \\\n              pax-utils \\\n readline-dev \\\n              sqlite-dev \\\n     tcl-dev \\\n              tk \\\n              tk-dev \\\n              zlib-dev \\\n              python2-dev \\\n              libffi-dev\n      - run:\n  name: Auth keys\n          command: |\n            ./node_modules/.bin/serverless config credentials \\\n       --provider aws \\\n            --key $AWS_KEY \\\n            --secret $AWS_SECRET\n      - run:\n   name: Deploy\n          command: ./node_modules/.bin/serverless deploy --verbose\n      - run:\n          name: Notify\n          command: ./.circleci/notify.sh\n\n build:\n    docker:\n      - image: signalnoise/base:10.13\n    steps:\n      - checkout\n      - run: ./.circleci/test.sh\n\nworkflows:\n  version: 2\n  test_and_build:\n    jobs:\n      - test:\n          context: sn-global\n'
    }, 
    u'lifecycle': u'not_running', 
    u'author_date': None, 
    u'committer_name': None
}