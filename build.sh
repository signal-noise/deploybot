#!/bin/bash
# build.sh
# 
# creates all the required vendor python packages using a docker container

if [ "./vendored" -ot "./requirements.txt" ]; then
    docker rm deploybot
    rm -rf ./vendored
    docker run --name deploybot -it -v ~/projects/deploybot:/project lambci/lambda:build-python3.7 /bin/sh -c "pip install -r /project/requirements.txt -t /project/vendored/"
    rm -rf ./vendored/enum*
else
    echo "Nothing to do"
fi