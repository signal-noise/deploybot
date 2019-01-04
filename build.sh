#!/bin/bash
# build.sh
# 
# creates all the required vendor python packages using a docker container

# No build needed if folder is newer than requirements file
if [ "./vendored" -ot "./requirements.txt" ]; then
    # Cleanup container and existing folder
    docker rm deploybot
    rm -rf ./vendored

    # Use docker to replicate Lambda environment; pip install all requirements to folder
    docker run --name deploybot -it -v ~/projects/deploybot:/project lambci/lambda:build-python3.7 /bin/sh -c "pip install -r /project/requirements.txt -t /project/vendored/"
    
    # Remove enum package that causes AttributeError: module 'enum' has no attribute 'IntFlag'
    rm -rf ./vendored/enum*
else
    echo "Nothing to do"
fi