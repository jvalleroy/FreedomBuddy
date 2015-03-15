#! /bin/sh
# -*- mode: sh; mode: auto-fill; fill-column: 80 -*-

PYTHONPATH=../:.:$PYTHONPATH
export PYTHONPATH

# do everything in multiple terminals.

# start fbuddy + cli client
x-terminal-emulator -e "python src/santiago_run.py" &

# start https client
x-terminal-emulator -e \
"python src/connectors/https/controller.py --listen" &
x-terminal-emulator -e \
"python src/connectors/https/controller.py --monitor" &

# start a browser for the monitor
x-terminal-emulator -e \
"sleep 5 && x-www-browser https://127.0.0.1:8081/freedombuddy" &

echo "Press return to quit."
read X
kill `ps | grep term | awk '{ print $1 }'`
