#!/bin/bash

# Copyright (C) 2020, Sardoodledom (github1@lotkit.org)
# All rights reserved.
#
# Although you can see the source code, it is not free and is
# protected by copyright. If you are interested in using it, please
# contact us at: github1@lotkit.org

PYTHON_BIN=python3
VIRTUALENV_BIN=virtualenv-3
PIP_BIN=pip3

pversion=$(${PYTHON_BIN} -V 2>&1 | grep -Po '(?<=Python )(.+)' | awk -F. '{printf("%03d%03d",$1,$2);}')


if [ -z "$pversion" ]; then
    echo "python3 not found" >&2
    exit 1
fi

re='^[0-9]+$'
if ! [[ $pversion =~ $re ]]; then
   echo "python3 version ($pversion) is not an integer" >&2
   exit 2
fi

if [ $pversion -gt 003006 ]; then
    echo "connexion does not work after Python 3.6! But I will continue!" >&2
fi


SOURCE="${BASH_SOURCE[0]}"
while [ -h "$SOURCE" ]; do # resolve $SOURCE until the file is no longer a symlink                                                                                                                        
  DIR="$( cd -P "$( dirname "$SOURCE" )" >/dev/null 2>&1 && pwd )"
  SOURCE="$(readlink "$SOURCE")"
  [[ $SOURCE != /* ]] && SOURCE="$DIR/$SOURCE" # if $SOURCE was a relative symlink, we need to resolve it relative to the path where the symlink file was located                                         
done
DIR="$( cd -P "$( dirname "$SOURCE" )" >/dev/null 2>&1 && pwd )"

if [ -e "${DIR}/venv" ]; then
    echo "dir '${DIR}/venv' does already exists!" >&2
    exit 3
fi


${VIRTUALENV_BIN} "${DIR}/venv"

source "${DIR}/venv/bin/activate"

${PIP_BIN} install -r "${DIR}/requirements.txt"


echo
echo
echo
echo To run the app:
echo source ${DIR}/venv/bin/activate
echo ${DIR}/run.py
