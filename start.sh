#! /bin/sh
# -*- mode: sh; mode: auto-fill; fill-column: 80 -*-
#
# do everything in multiple terminals.

PYTHONPATH=../:.:$PYTHONPATH
export PYTHONPATH

# start fbuddy + cli client
x-terminal-emulator -e "python src/santiago_run.py $@" &
echo $! >> santiago.pid


# start https client
x-terminal-emulator -e \
"python src/connectors/https/controller.py --listen" &
echo $! >> santiago.pid

x-terminal-emulator -e \
"python src/connectors/https/controller.py --monitor" &
echo $! >> santiago.pid


# start a browser for the monitor
x-terminal-emulator -e \
"sleep 5 && x-www-browser https://127.0.0.1:8081/freedombuddy" &
echo $! >> santiago.pid


# and bail when we're done.
echo "Stop the Santiago process to save data and then press return to quit."
read X
kill `cat santiago.pid` > /dev/null 2>&1
rm santiago.pid
