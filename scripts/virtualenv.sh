#!/usr/bin/env bash

DIR=$(dirname $0)
cd ${DIR}/..
python -m virtualenv -p python3.8 ENV
