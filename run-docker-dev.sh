#!/bin/bash

docker run --rm \
  --name medialab-manager-dev \
  -p 4801:4800 \
  -v $(pwd)/app:/code/app \
  -v $(pwd)/config.json:/code/config.json \
  -v $(pwd)/requirements.txt:/code/requirements.txt \
  medialab-manager \
  uvicorn app.main:app --host 0.0.0.0 --port 4800 --reload 