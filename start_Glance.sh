#!/bin/bash
#

process=${1:-"launcher"}
venv=${2:-"no"}

cd $(dirname "$0")
if [ "$venv" == "venv" ]; then
  . venv/bin/activate
fi
export GOOGLE_APPLICATION_CREDENTIALS=~/.credentials/sa_cred.json
python3 ${process}.py $3 $4 $5
