"""Shared utilities.

Currently contains a bunch of errors and config-file shortcuts.

"""

import ConfigParser as configparser


# each of these ends in "/" so we don't prefix file names with /.
# what would happen if the directory were null then?
# https://github.com/ValveSoftware/steam-for-linux/issues/3671 would happen.
CONFIG_DIRS = ("/usr/share/santiago/",
                "~/.santiago/",
                "./data/")


def load_default_configs():
    """Load production.cfg from each of the CONFIG_DIRS."""

    return load_configs([x + "production.cfg" for x in CONFIG_DIRS])


def load_configs(config_files):
    """Returns data from the named config file."""

    config = configparser.ConfigParser()
    config.read(config_files)
    return config


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
    """The HTTPS connector shouldn't allow concurrent PUT + DELETE requests."""

    pass
