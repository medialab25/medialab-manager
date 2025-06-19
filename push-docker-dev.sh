#!/bin/bash

docker login registry.spongnet.uk -u mediadev -p 'MediaMonkey25!!'
docker build -t registry.spongnet.uk/medialab-manager:latest-dev .
docker push registry.spongnet.uk/medialab-manager:latest-dev
