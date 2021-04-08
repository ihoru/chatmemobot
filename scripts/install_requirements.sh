#!/usr/bin/env bash

DIR=$(dirname $0)
cd ${DIR}/..
if [[ ! -d $PWD/ENV ]]; then
  $PWD/scripts/virtualenv.sh
fi
F=''
if [[ -n $1 ]]; then
  F='-to-freeze'
fi
source $PWD/ENV/bin/activate
pip install --compile -r $PWD/requirements$F.txt
