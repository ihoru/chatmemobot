#!/usr/bin/env bash

DIR=$(dirname $0)
cd ${DIR}/..
source $PWD/ENV/bin/activate
python reminder.py $@ >> logs/reminder.log 2>&1
