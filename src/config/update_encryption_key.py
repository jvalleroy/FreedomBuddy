#! /usr/bin/env python # -*- mode: auto-fill; fill-column: 80 -*-
import sys
import ConfigParser as configparser
import gnupg

config_file_to_update = gpg_home_directory = email_of_key_to_use = public_key= ""

if len(sys.argv) >= 3:
    config_file_to_update = sys.argv[1]
    gpg_home_directory = sys.argv[2]
if len(sys.argv) > 3:
    email_of_key_to_use = sys.argv[3]

gpg = gnupg.GPG(gnupghome=gpg_home_directory)
public_keys = gpg.list_keys(secret=True)
if(email_of_key_to_use!=""):
    for key in public_keys:
        for uid in key['uids']:
            if(uid.endswith("<"+email_of_key_to_use+">")):
                public_key = key['fingerprint']
else:
    public_key = public_keys[0]['fingerprint']

config = configparser.ConfigParser()
config.read(config_file_to_update)
config.set("pgpprocessor", "KEYID", public_key)


with open(config_file_to_update, "wb") as new_config:
 	config.write(new_config)
