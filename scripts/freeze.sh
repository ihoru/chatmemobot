#!/usr/bin/env bash

DIR=$(dirname $0)
cd ${DIR}/..
source $PWD/ENV/bin/activate
pip freeze --local -r $PWD/requirements-to-freeze.txt | grep -v pkg-resources==0.0.0 | tee $PWD/requirements.txt
