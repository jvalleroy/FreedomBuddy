#! /bin/sh
# -*- mode: sh; mode: auto-fill; fill-column: 80 -*-
#
# do everything in multiple terminals.

PYTHONPATH=.:$PYTHONPATH
export PYTHONPATH

#
# kill any running servers/clients when exiting.
cleanup() {
    python src/connectors/cli/controller.py --stop

    # don't die if we can't kill everything.
    for pid in $cliClient $httpsClient $httpsMonitor $browser
    do
        kill $pid
        if [ $? -eq 0 ]
        then
            sed -i "/^$pid/d" santiago.pid
        fi
    done
}
trap cleanup EXIT

#
# start fbuddy + cli client
python src/santiago_run.py $@ >> santiago_run.out 2>&1 &
cliClient=$!
echo "$cliClient # cli client: `date`"  >> santiago.pid

#
# start https client
python src/connectors/https/controller.py --listen >> santiago_http-listener.out 2>&1 &
httpsClient=$!
echo "$httpsClient # https client: `date`" >> santiago.pid

python src/connectors/https/controller.py --monitor >> santiago_http-monitor.out 2>&1 &
httpsMonitor=$!
echo "$httpsMonitor # https monitor: `date`" >> santiago.pid

#
# start a browser for the monitor
# (sleep 5 && x-www-browser https://localhost:8081/freedombuddy >> santiago_browser.out) 2>&1 &
# browser=$!
# echo "$browser # browser: `date`" >> santiago.pid

#
# and pause to let the processes run.
echo "Stop the Santiago process to save data and then press return to quit."
read X
