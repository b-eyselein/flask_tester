#!/usr/bin/env bash

# run server in background
cd ./app || exit

python server.py > ../server_logs.txt 2>&1 &

sleep 2

cd .. || exit

python flask_test_executor.py

ls -al

echo "X"

cat result.json

echo "Y"

# stop server (background job)
kill %1
