#!/usr/bin/env bash

DIR=$(dirname $0)
cd ${DIR}/..
source $PWD/ENV/bin/activate
python main.py $@ >> logs/main.log 2>&1
