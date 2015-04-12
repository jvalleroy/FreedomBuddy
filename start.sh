#! /bin/sh
# -*- mode: sh; mode: auto-fill; fill-column: 80 -*-
#
# do everything in multiple terminals.

PYTHONPATH=../:.:$PYTHONPATH
export PYTHONPATH

#
# kill any running servers/clients when exiting.
cleanup() {
    kill $cliClient $httpsClient $httpsMonitor $browser > /dev/null 2>&1
    cat santiago.pid | sed "/^($cliClient|$httpsClient|$httpsMonitor|$browser)/d" > santiago.pid
}
trap cleanup EXIT

#
# start fbuddy + cli client
x-terminal-emulator -e "python src/santiago_run.py $@" &
cliClient=$!
echo "$cliCilent # cli client: `date`"  >> santiago.pid

#
# start https client
x-terminal-emulator -e \
"python src/connectors/https/controller.py --listen" &
httpsClient=$!
echo "$httpsClient # https client: `date`" >> santiago.pid

x-terminal-emulator -e \
"python src/connectors/https/controller.py --monitor" &
htpsMonitor=$!
echo "$httpsMonitor # https monitor: `date`" >> santiago.pid

#
# start a browser for the monitor
x-terminal-emulator -e \
"sleep 5 && x-www-browser https://localhost:8081/freedombuddy" &
browser=$!
echo "$browser # browser: `date`" >> santiago.pid

#
# and pause to let the processes run.
echo "Stop the Santiago process to save data and then press return to quit."
read X
