#! /usr/bin/env python
# -*- mode: python; mode: auto-fill; fill-column: 80; -*-

"""Starts a test FreedomBuddy service.

Good for testing that it'll actually run and start up.  By default, it'll start
listening for connections on ``https://localhost:8080``.  It'll be hosting the
FreedomBuddy service for itself and be able to learn and provide its own
services to itself.  That will allow you to add additional services as
necessary, that you can then provide to yourself or others.

"""

import ConfigParser as configparser
import logging
from optparse import OptionParser
import sys
import src.utilities as utilities
import webbrowser

import src.santiago as santiago


config_dirs = ("/usr/share/santiago/",
                "~/.santiago/",
                "./data/")


def parse_args(args):
    """Interpret args passed in on the command line."""

    parser = OptionParser()

    parser.add_option("-v", "--verbose", dest="verbose", action="count",
                      help="""\
Can be given multiple times to increase logging level.  Once means show
FreedomBuddy logging messages.  Twice means show connector logging messages as
well.""")

    parser.add_option("-c", "--config", dest="config",
                      default="data/production.cfg",
                      help="""The configuration file to use.""")

    parser.add_option("-d", "--default-services", dest="default_services",
                      action="store_true", help="""\
Whether to reset the list of hosted and consumed services to the default.""")

    parser.add_option("-f", "--forget", dest="forget_services",
                      action="store_true", help="""\
If set, don't store service data when exiting.

Useful if you want to test or experiment with new service configurations,
without overwriting your existing data.""")

    parser.add_option("-t", "--trace", dest="trace", action="store_true",
                      help="Drop into the debugger when starting FreedomBuddy.")

    return parser.parse_args(args)

def load_config(config):
    """Load data from the specified configuration file."""

    listify_string = lambda x: [item.strip() for item in x.split(",")]

    config = utilities.load_config(config)

    mykey = utilities.safe_load(config, "pgpprocessor", "keyid", 0)
    protocols = listify_string(
        utilities.safe_load(config, "connectors", "protocols"))
    connectors = {}
    force_sender = utilities.safe_load(config, "connectors", "force_sender")

    # services to host and consume
    url = utilities.safe_load(config, "general", "url")

    if protocols == ['']:
        raise RuntimeError("No protocols detected.  Have you run 'make'?")

    # loop through the protocols, finding connectors each protocol uses
    # load the settings for each connector.
    for protocol in protocols:
        protocol_connectors = listify_string(
            utilities.safe_load(config, protocol, "connectors"))

        if not protocol_connectors:
            continue

        for connector in protocol_connectors:
            connectors[connector] = dict(
                utilities.safe_load(config, connector, None, {}))

    return mykey, protocols, connectors, force_sender, url

def configure_connectors(protocols, connectors):

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

def load_services(conf_dirs):
    """If we can't find a service file, load the default services.

    This is handy the first time we boot the system.

    """
    for config_dir in reversed(conf_dirs):
        mykey_config = os.exists(expanduser(config_dir + mykey + ".dat"))
        if mykey_config:
            break

    if mykey_config:
        hosting = consuming = None
    else:
        service = "freedombuddy"
        hosting = { mykey: { service: [url],
                             service + "-monitor" : [url + "/" + service] } }
        consuming = { mykey: { service: [url],
                             service + "-monitor" : [url + "/" + service] } }

    return hosting, consuming


if __name__ == "__main__":

    (options, args) = parse_args(sys.argv)

    if options.trace:
        import pdb; pdb.set_trace()

    if options.verbose > 0:
        logging.getLogger().setLevel(logging.DEBUG)
        logging.getLogger("cherrypy.error").setLevel(logging.CRITICAL)
    if options.verbose > 1:
        logging.getLogger("cherrypy.error").setLevel(logging.DEBUG)

    # load configuration settings
    if options.config:
        mykey, protocols, connectors, force_sender, url = (
            load_config(options.config))
    else:
        config = {}
        for config_dir in config_dirs:
            config = (merge_config(config_dir + "production.cfg", config))
        mykey = config_options["mykey"]
        protocols = config_options["protocols"]
        connectors = config_options["connectors"]
        force_sender = config_options["force_sender"]
        url = config_options["url"]

    # create listeners and senders
    listeners, senders, monitors = configure_connectors(protocols, connectors)

    # if we can't find a config file, load default services.
    hosting, consuming = load_services(config_dirs)

    santiago.debug_log("Santiago!")
    freedombuddy = santiago.Santiago(listeners, senders, hosting, consuming,
                                     my_key_id=mykey, monitors=monitors,
                                     save_dir="data",
                                     force_sender=force_sender)

    # run
    with freedombuddy:
        if "https" in protocols:
            webbrowser.open_new_tab(url + "/freedombuddy")

    santiago.debug_log("Santiago startup finished!")
