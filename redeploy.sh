#!/bin/bash

cd "$(dirname "$0")"
source venv/bin/activate

# Find and kill the running app (if any)
PID=$(ps aux | grep 'python -m src.web.app' | grep -v grep | awk '{print $2}')
if [ ! -z "$PID" ]; then
    echo "Killing existing app process: $PID"
    kill $PID
    sleep 2
fi

# Start the app
PYTHONPATH=$(pwd) nohup python -m src.web.app &
NEWPID=$!
echo "Started new app process: $NEWPID"

# Follow the logs
sleep 1
tail -f nohup.out 