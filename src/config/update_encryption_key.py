#! /usr/bin/env python
# -*- mode: python; mode: auto-fill; fill-column: 80 -*-

import ConfigParser as configparser
import gnupg
import sys
import time

if len(sys.argv) >= 3:
    config_file_to_update = sys.argv[1]
    gpg_home_directory = sys.argv[2]
if len(sys.argv) > 3:
    email_of_key_to_use = sys.argv[3]

now = time.time()
config_file_to_update = gpg_home_directory = email_of_key_to_use = public_key= ""
gpg = gnupg.GPG(gnupghome=gpg_home_directory)
now = time.time()
public_keys = gpg.list_keys(secret=True)

for key in public_keys:
    for uid in key['uids']:
        if (not email_of_key_to_use) or (uid.endswith("<"+email_of_key_to_use+">")):
            public_key = key['fingerprint']

    # pick the first not-expired (matching) key we find.
    # if we don't find a valid key, pick the last key we checked.
    if public_key and int(key["expires"]) > now:
        break

config = configparser.ConfigParser()
config.read(config_file_to_update)
config.set("general", "keyid", public_key)

with open(config_file_to_update, "wb") as new_config:
    config.write(new_config)
