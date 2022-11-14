#!/usr/bin/env bash

# run server in background
cd ./app || exit

python server.py >../server_logs.txt 2>&1 &

sleep 1

# run tester
cd .. || exit

timeout -s KILL 30 python flask_test_executor.py

# stop server (background job)
kill %1
