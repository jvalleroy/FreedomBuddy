"""Tests for the CLI controller.

TODO remove literal dictionaries, replace with ast.literal_eval.
Much easier to read.

"""

import ast
from datetime import datetime
import gnupg
import logging
import time
import unittest
import threading

import src.connectors.cli.controller as controller
from src.santiago import Santiago
import src.utilities as utilities

class CliListener(unittest.TestCase):
    """Test main code call."""

    def setUp(self):
        self.gpg = gnupg.GPG(gnupghome='src/tests/data/test_gpg_home')
        self.keyid = utilities.load_config(
            "src/tests/data/test_gpg.cfg").get("pgpprocessor", "keyid")
        self.test_keyid = "1" * 40
        self.original_update_time = time.time()
        a_service = Santiago.SERVICE_NAME

        hosting = {
            self.keyid: {
                a_service:
                    ["http://127.0.0.1"],
                Santiago.update_time(a_service):
                    str(self.original_update_time) }}
        consuming = {
            self.keyid: {
                a_service:
                    ["http://127.0.0.2"],
                Santiago.update_time(a_service):
                    str(self.original_update_time) }}

        self.santiago = Santiago(
            hosting = hosting,
            consuming = consuming,
            my_key_id = self.keyid,
            gpg = self.gpg,
            save_dir='src/tests/data/CLI_Controller')

        controller.SANTIAGO_INSTANCE = self.santiago
        self.bjsonRpcInstance = controller.BjsonRpcHost(None)

    def test_get_hosting_clients(self):
        """Confirm hosting clients are returned correctly."""

        self.assertEqual(
            {"clients": [self.keyid]},
            ast.literal_eval(self.bjsonRpcInstance._change("list", 1)))

    def test_get_hosting_services(self):
        """Confirm services we host for client are returned correctly."""

        self.assertEqual(
            {"services": {"freedombuddy": ["http://127.0.0.1"], "freedombuddy-update-timestamp": str(self.original_update_time)}, "client": self.keyid},
            ast.literal_eval(self.bjsonRpcInstance._change("list", 1, self.keyid)))

    def test_get_hosting_service_locations(self):
        """Confirm locations we host for client x service are returned correctly."""
        self.assertEqual(
            '{"client": "'+self.keyid+'", "locations": ["http://127.0.0.1"], "service": "freedombuddy"}',
            self.bjsonRpcInstance._change("list", 1, self.keyid, "freedombuddy"))

    def test_get_consuming_clients(self):
        """Confirm consuming hosts are returned correctly."""
        self.assertEqual(
            '{"hosts": ["'+self.keyid+'"]}',
            self.bjsonRpcInstance._change("list", 0, None))

    def test_get_consuming_services(self):
        """Confirm services we consume from host are returned correctly."""
        self.assertEqual(
            '{"services": {"freedombuddy": ["http://127.0.0.2"], "freedombuddy-update-timestamp": "'+str(self.original_update_time)+'"}, "host": "'+self.keyid+'"}',
            self.bjsonRpcInstance._change("list", 0, self.keyid))

    def test_get_consuming_service_locations(self):
        """Confirm locations we consume from host x service are returned correctly."""
        self.assertEqual(
            '{"host": "'+self.keyid+'", "locations": ["http://127.0.0.2"], "service": "freedombuddy"}',
            self.bjsonRpcInstance._change("list", 0, self.keyid, "freedombuddy"))

    def test_add_hosting_client(self):
        """Confirm client is added to hosting list."""
        self.bjsonRpcInstance._change("add", 1, self.test_keyid)
        self.assertEqual(
            '{"clients": ["'+self.test_keyid+'", "'+self.keyid+'"]}',
            self.bjsonRpcInstance._change("list", 1, None))

    def test_add_hosting_client_service(self):
        """Confirm service is added for client."""

        time_to_use = str(self.original_update_time+1)
        self.bjsonRpcInstance._change("add", 1, self.test_keyid,
                                      "freedombuddy", update = time_to_use)
        self.assertEqual(
            '{"services": {"freedombuddy": [], "freedombuddy-update-timestamp": "'+time_to_use+'"}, "client": "'+self.test_keyid+'"}',
            self.bjsonRpcInstance._change("list", 1, self.test_keyid))

    def test_add_hosting_service_locations(self):
        """Confirm location is added for service x client."""

        time_to_use = str(self.original_update_time+1)
        self.bjsonRpcInstance._change(
            "add", 1, self.test_keyid, "freedombuddy", "http://127.0.0.1",
            time_to_use)
        self.assertEqual(
            '{"client": "'+self.test_keyid+'", "locations": ["http://127.0.0.1"], "service": "freedombuddy"}',
            self.bjsonRpcInstance._change("list", 1, self.test_keyid, "freedombuddy"))
        self.assertEqual(
            '{"client": "'+self.test_keyid+'", "locations": "'+time_to_use+'", "service": "freedombuddy-update-timestamp"}',
            self.bjsonRpcInstance._change(
                "list", 1, self.test_keyid, "freedombuddy-update-timestamp"))

    def test_add_consuming_client(self):
        """Confirm client is added to consuming list."""
        self.bjsonRpcInstance._change("add", 0, self.test_keyid)
        self.assertEqual(
            '{"hosts": ["'+self.test_keyid+'", "'+self.keyid+'"]}',
            self.bjsonRpcInstance._change("list", 0, None))

    def test_add_consuming_client_service(self):
        """Confirm service is added for client."""
        time_to_use = str(self.original_update_time+1)
        self.bjsonRpcInstance._change(
            "add", 0, self.test_keyid, "freedombuddy", update = time_to_use)
        self.assertEqual(
            '{"services": {"freedombuddy": [], "freedombuddy-update-timestamp": "'+time_to_use+'"}, "host": "'+self.test_keyid+'"}',
            self.bjsonRpcInstance._change("list", 0, self.test_keyid))

    def test_add_consuming_service_locations(self):
        """Confirm location is added for service x client."""
        time_to_use = str(self.original_update_time+1)
        self.bjsonRpcInstance._change(
            "add", 0, self.test_keyid, "freedombuddy", "http://127.0.0.1",
            time_to_use)
        self.assertEqual(
            '{"host": "'+self.test_keyid+'", "locations": ["http://127.0.0.1"], "service": "freedombuddy"}',
            self.bjsonRpcInstance._change(
                "list", 0, self.test_keyid, "freedombuddy"))
        self.assertEqual(
            '{"host": "'+self.test_keyid+'", "locations": "'+time_to_use+'", "service": "freedombuddy-update-timestamp"}',
            self.bjsonRpcInstance._change(
                "list", 0, self.test_keyid, "freedombuddy-update-timestamp"))

    def test_remove_hosting_client(self):
        """Confirm hosting client is removed."""
        self.bjsonRpcInstance._change("remove", 1, self.keyid)
        self.assertEqual(
            '{"clients": []}',
            self.bjsonRpcInstance._change("list", 1, None))

    def test_remove_hosting_service(self):
        """Confirm hosting service is removed."""
        self.bjsonRpcInstance._change("remove", 1, self.keyid, "freedombuddy")
        self.assertEqual(
            '{"services": {}, "client": "'+self.keyid+'"}',
            self.bjsonRpcInstance._change("list", 1, self.keyid))

    def test_remove_hosting_location(self):
        """Confirm hosting location is removed."""
        self.bjsonRpcInstance._change(
            "remove", 1, self.keyid, "freedombuddy", "http://127.0.0.1")
        self.assertEqual(
            {"services": {"freedombuddy": [], "freedombuddy-update-timestamp": str(self.original_update_time)}, "client": self.keyid},
            dict(self.bjsonRpcInstance._change("list", 1, self.keyid)))

    def test_remove_consuming_client(self):
        """Confirm consuming client is removed."""
        self.bjsonRpcInstance._change("remove", 0, self.keyid)
        self.assertEqual(
            {"hosts": []},
            dict(self.bjsonRpcInstance._change("list", 0, None)))

    def test_remove_consuming_service(self):
        """Confirm consuming service is removed."""
        self.bjsonRpcInstance._change("remove", 0, self.keyid, "freedombuddy")
        self.assertEqual(
            {'services': {}, 'host': self.keyid},
            ast.literal_eval(
                self.bjsonRpcInstance._change("list", 0, self.keyid)))

    def test_remove_consuming_location(self):
        """Confirm consuming location is removed."""
        self.bjsonRpcInstance._change(
            "remove", 0, self.keyid, "freedombuddy", "http://127.0.0.2")
        self.assertEqual(
            str({"services":
                     { "freedombuddy": [],
                       "freedombuddy-update-timestamp":
                           str(self.original_update_time)},
                 "host": self.keyid}),
            self.bjsonRpcInstance._change("list", 0, self.keyid))

class CliSender(unittest.TestCase):
    """Test main code call."""
    def setUp(self):
        self.gpg = gnupg.GPG(gnupghome='src/tests/data/test_gpg_home')
        self.keyid = utilities.load_config(
            "src/tests/data/test_gpg.cfg").get("pgpprocessor", "keyid")
        self.test_keyid = "1111111111111111111111111111111111111111"
        self.santiago = Santiago(
            hosting = {
                self.keyid: {
                    Santiago.SERVICE_NAME: ["http://127.0.0.1"],
                    Santiago.SERVICE_NAME+'-update-timestamp': None }},
            consuming = {
                self.keyid: {
                    Santiago.SERVICE_NAME: ["http://127.0.0.2"],
                    Santiago.SERVICE_NAME+'-update-timestamp': None }},
            my_key_id = self.keyid,
            gpg = self.gpg,
            save_dir='src/tests/data/CLI_Controller')
        self.cliSender = controller.CliSender(
            santiago = self.santiago,
            https_sender = ("python src/connectors/https/controller.py " +
                            "--outgoing $REQUEST --destination $DESTINATION"),
            cli_sender = "echo $DESTINATION $REQUEST")

if __name__ == "__main__":
    logging.disable(logging.CRITICAL)
    unittest.main()
