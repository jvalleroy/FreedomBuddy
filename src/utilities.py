"""Shared utilities.

Currently contains a bunch of errors and config-file shortcuts.

"""

import ConfigParser as configparser

def load_config(configfile):
    """Returns data from the named config file."""

    config = configparser.ConfigParser()
    config.read([configfile])
    return config

def get_config_values(config):
    """Load data from the specified configuration file.

    Load None instead of erroring."""

    listify_string = lambda x: [item.strip() for item in x.split(",")]

    mykey = safe_load(config, "pgpprocessor", "keyid", 0)
    protocols = listify_string(
        safe_load(config, "connectors", "protocols"))
    connectors = {}
    force_sender = safe_load(config, "connectors", "force_sender")
    url = safe_load(config, "general", "url")

    if protocols == ['']:
        raise RuntimeError("No protocols detected.  Have you run 'make'?")

    # loop through the protocols, finding connectors each protocol uses
    # load the settings for each connector.
    for protocol in protocols:
        protocol_connectors = listify_string(
            safe_load(config, protocol, "connectors"))

        if not protocol_connectors:
            continue

        for connector in protocol_connectors:
            connectors[connector] = dict(
                safe_load(config, connector, None, {}))

    return mykey, protocols, connectors, force_sender, url

def merge_config(config_file, config_options):
    """Override loaded config data with new data."""

    all_keys = ("mykey", "protocols", "connectors", "force_sender", "url")

    new_data = dict(zip(all_keys, get_config_values(config_file)))

    for option in all_keys:
        if new_data[option] is not None:
            config_options[option] = new_data[option]

    return config_options

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

def multi_sign(message, gpg, keyid, iterations=3):
    """Sign a message several times with a specified key."""

    messages = [message]

    if not gpg:
        raise GPGNotSpecifiedError
    if not keyid:
        raise GPGKeyNotSpecifiedError

    for i in range(iterations):
        messages.append(str(gpg.sign(messages[i])))

    return messages

def safe_load(config, section, key=None, default=None):
    """Safely load data from a configuration file.

    If the key does not exist in the section, or the section does not
    exist, return the default value instead of raising an exception.

    """
    try:
        if key is not None:
            return config.get(section, key)
        else:
            return config.items(section)
    except (configparser.NoSectionError, configparser.NoOptionError):
        return default

class SignatureError(Exception):
    """Base class for signature-related errors."""

    pass

class InvalidSignatureError(SignatureError):
    """The signature in this message is cryptographically invalid."""

    pass

class UnwillingHostError(SignatureError):
    """The current process isn't willing to host a service for the client."""

    pass

class GPGNotSpecifiedError(Exception):
    """The gpg object should be explicitly created when FB is encrypting data"""

    pass

class GPGKeyNotSpecifiedError(Exception):
    """The gpg object should be explicitly created when FB is encrypting data"""

    pass

class HTTPSConnectorError(Exception):
    """Base class for HTTPS Connector errors"""

    pass

class HTTPSConnectorInvalidCombinationError(HTTPSConnectorError):
    """The HTTPS connector requests shouldn't allow both PUT & DELETE at the same time"""

    pass
