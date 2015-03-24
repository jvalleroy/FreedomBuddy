#! /usr/bin/env python
# -*- mode: python; mode: auto-fill; fill-column: 80; -*-

"""Starts a test FreedomBuddy service.

Good for testing that it'll actually run and start up.  By default, it'll start
listening for connections on ``https://localhost:8080``.  It'll be hosting the
FreedomBuddy service for itself and be able to learn and provide its own
services to itself.  That will allow you to add additional services as
necessary, that you can then provide to yourself or others.

"""

import logging
from optparse import OptionParser
import os
import sys
import src.utilities as utilities
import webbrowser

import src.santiago as santiago


def parse_args(args):
    """Interpret args passed in on the command line."""

    parser = OptionParser()

    parser.add_option("-v", "--verbose", dest="verbose", action="count",
                      help="""\
Can be given multiple times to increase logging level.  Once means show
FreedomBuddy logging messages.  Twice means show connector logging messages as
well.""")

    parser.add_option("-c", "--config", dest="config",
                      help="""The configuration file to use.""")

    parser.add_option("-f", "--forget", dest="forget_services",
                      action="store_true", help="""\
If set, don't store service data when exiting.

Useful if you want to test or experiment with new service configurations,
without overwriting your existing data.""")

    parser.add_option("-t", "--trace", dest="trace", action="store_true",
                      help="""\
Drop into the debugger when starting FreedomBuddy.""")

    return parser.parse_args(args)


def listify_string(astring, delim=","):
    """Transform a string into a list of 1 or more elements."""

    return [item.strip() for item in astring.split(delim)]


def load_connectors(protocols, config_data):
    """Loop through the protocols, loading settings for each used connector.

    We're combining disparate connector settings from the config file into a
    single dictionary of connectors.

    """
    connectors = {}

    for protocol in protocols:
        protocol_connectors = listify_string(
            utilities.safe_load(config_data, protocol, "connectors"))

        if not protocol_connectors:
            continue

        for connector in protocol_connectors:
            connectors[connector] = dict(
                utilities.safe_load(config_data, connector, None, {}))

    return connectors

def configure_connectors(protocols, connectors):
    """Extract the supported connectors per protocol."""

    listeners, senders, monitors = {}, {}, {}

    for protocol in protocols:
        for connector in connectors:
            if connector == protocol + "-listener":
                listeners[protocol] = dict(connectors[protocol + "-listener"])
            elif connector == protocol + "-sender":
                senders[protocol] = dict(connectors[protocol + "-sender"])
            elif connector == protocol + "-monitor":
                monitors[protocol] = dict(connectors[protocol + "-monitor"])

    return listeners, senders, monitors


def load_services(CONF_DIRS, config_data):
    """If we can't find a service file, load the default services.

    This is handy the first time we boot the system.

    """
    for config_dir in reversed(CONF_DIRS):
        mykey_config = os.path.exists(os.path.expanduser(
                config_dir + mykey + ".dat"))
        if mykey_config:
            break

    if mykey_config:
        hosting = consuming = None
    else:
        service = "freedombuddy"
        listener_url = "https://localhost:{0}".format(
            utilities.safe_load(
                config_data,"https-listener", "socket_port", 8080))
        monitor_url = "https://localhost:{0}".format(
            utilities.safe_load(
                config_data,"https-listener", "socket_port", 8081))


        hosting = {mykey: {service: [listener_url],
                           service + "-monitor" : [monitor_url + "/" + service]}}
        consuming = {mykey: {service: [listener_url],
                             service + "-monitor" : [monitor_url + "/" + service]}}

    return hosting, consuming


if __name__ == "__main__":

    (options, args) = parse_args(sys.argv)

    if options.trace:
        import pdb
        pdb.set_trace()

    if options.verbose > 0:
        logging.getLogger().setLevel(logging.DEBUG)
        logging.getLogger("cherrypy.error").setLevel(logging.CRITICAL)
    if options.verbose > 1:
        logging.getLogger("cherrypy.error").setLevel(logging.DEBUG)

    # load configuration settings
    config_data = (utilities.load_configs(options.config) if options.config else
                   utilities.load_default_configs())

    mykey = config_data.get("general", "keyid")
    protocols = listify_string(config_data.get("connectors", "protocols"))
    connectors = load_connectors(protocols, config_data)
    force_sender = config_data.get("connectors", "force_sender")

    # create listeners and senders
    listeners, senders, monitors = configure_connectors(protocols, connectors)

    # if we can't find a service config file, load default services.
    hosting, consuming = load_services(utilities.CONFIG_DIRS, config_data)

    santiago.debug_log("Santiago!")
    freedombuddy = santiago.Santiago(
        listeners, senders, hosting, consuming,
        my_key_id=mykey, monitors=monitors,
        save_dir="data", save_services=(not options.forget_services),
        force_sender=force_sender)

    # run
    with freedombuddy:
        if "https" in protocols:
            webbrowser.open_new_tab(hosting[mykey]["freedombuddy-monitor"])

    santiago.debug_log("Santiago startup finished!")
