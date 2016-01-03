#! /bin/sh
# -*- mode: sh; mode: auto-fill; fill-column: 80 -*-
#
# do everything in multiple terminals.

PYTHONPATH=.:$PYTHONPATH
export PYTHONPATH
verbose=0

#
# kill any running servers/clients when exiting.
cleanup() {
    if [ "$verbose" = "1" ]
    then
        python src/connectors/cli/controller.py --stop
    else
        python src/connectors/cli/controller.py --stop 2>/dev/null
    fi

    # don't die if we can't kill everything.
    for pid in $cliClient $httpsClient $httpsMonitor $browser
    do
        if [ "$verbose" = "1" ]
        then
            echo -n "Killing ${pid}... "
        fi

        ps $pid | grep $pid 2>&1 > /dev/null

        if [ "$?" = "0" ]
        then
            kill $pid
        else
            true
        fi

        if [ "$?" = "0" ]
        then
            if [ "$verbose" = "1" ]
            then
                echo "Done."
            fi
            sed -i "/^$pid/d" santiago.pid
        fi
    done
}
trap cleanup EXIT

loadPids() {
    cliClient=`grep "cli client" santiago.pid | awk '{ print $1 }'`
    httpsClient=`grep "https client" santiago.pid | awk '{ print $1 }'`
    httpsMonitor=`grep "https monitor" santiago.pid | awk '{ print $1 }'`
    browser=`grep "browser" santiago.pid | awk '{ print $1 }'`
}

for arg in $@
do
    if [ "$arg" = "--verbose" ]
    then
        verbose=1
    fi
    if [ "$arg" = "--stop" ]
    then
        stop=1
    fi
done

if [ "$stop" = "1" ]
then
    loadPids
    exit
fi

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
