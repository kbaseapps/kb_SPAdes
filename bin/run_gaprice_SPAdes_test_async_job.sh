#!/bin/bash
script_dir=$(dirname "$(readlink -f "$0")")
export PYTHONPATH=$script_dir/../lib:$PATH:$PYTHONPATH
python -u $script_dir/../lib/gaprice_SPAdes_test/gaprice_SPAdes_testServer.py $1 $2 $3
