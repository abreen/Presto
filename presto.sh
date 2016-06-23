#!/bin/bash

PYTHONS='python python3'

for p in $PYTHONS; do
    pypath=$(which $p)

    if [[ $? -eq 0 ]]; then
        echo presto: python: using $pypath
        $pypath -c 'import presto; presto.main()'
        exit 0
    fi
done

echo $0: error: could not find a Python interpreter
exit 1
