#! /usr/bin/env python
# -*- mode: python; mode: auto-fill; fill-column: 80 -*-

"""Tests for the initial start-up functions.

These functions are mostly tested by testing completed on main Santiago
functionality but these should be tested independently as well.

"""

import shlex
import subprocess
import time
import unittest

import src.santiago_run as santiago_run
import src.utilities as utilities

class ParseArgs(unittest.TestCase):
    """Validates arguments passed to command line."""

    def test_default_values_returned_when_no_arguments_passed(self):
        (self.options, self.arguments) = santiago_run.parse_args([""])
        self.assertEqual(None, self.options.trace)
        self.assertEqual(None, self.options.verbose)
        self.assertEqual(None, self.options.forget_services)

    def test_values_returned_when_short_arguments_passed_in(self):
        (self.options, self.arguments) = santiago_run.parse_args(
            ["-c","te","-v","-f","-t"])
        self.assertEqual("te", self.options.config)
        self.assertEqual(1, self.options.verbose)
        self.assertEqual(1, self.options.trace)
        self.assertEqual(1, self.options.forget_services)


class EndToEnd(unittest.TestCase):
    """TestCase superclass to set up an end-to-end test.

    This class starts a Santiago server and client that can communicate amongst
    themselves.

    """
    def setUp(self, *args, **kwargs):
        super(EndToEnd, self).setUp(*args, **kwargs)
        self.fbuddy = subprocess.Popen("./start.sh".split())
        time.sleep(2)

    def tearDown(self, *args, **kwargs):
        super(EndToEnd, self).tearDown(*args, **kwargs)
        self.fbuddy.terminate()

    def load_default_configs(self):
        return utilities.load_config([x + "test.cfg"
                                       for x in utilities.CONFIG_DIRS])

class RoundTrip(EndToEnd):
    """Run a client->server->client round-trip test.

    1. The client will request that the server adds a new service location for
       another client (with its same id, effectively the same cilent).

    2. The server will add that service location.

    3. The client will then request an updated service location from the server.

    4. The server will reply to the client with the updated location.

    This verifies that clients and servers can communicate.  The one trick here
    is that the client adds a service location for itself, so the client is
    effectively hosting and consuming its own service.  This is a measure of
    convenience that saves us from having to run multiple clients with separate
    key ids, at one time.

    If there's ever an issue with client1<->server1<->server2<->client2
    communication, we'll add those tests too.  However, the only big difference
    is that we're exercising different parts of the encryption library, so it's
    not a high-value test at this time.

    """
    def setUp(self, *args, **kwargs):
        super(RoundTrip, self).setUp(*args, **kwargs)

        self.config = self.load_default_configs()
        self.mykey = utilities.safe_load(self.config, "general", "keyid")
        if not self.mykey:
            raise RuntimeError("No key configured for testing.")

    def test_add_service(self):
        commands = [
            "python src/query.py -a add --hosting --key {0} \
--service freedombuddy --location https://example.invalid",
            "python src/query.py --query --key {0} --service freedombuddy --hosting",
            "python src/query.py -a list --consuming --key {0} --service freedombuddy"]
        import pprint
        for command in commands:
            process = subprocess.Popen(
                shlex.split(command.format(self.mykey)),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE)

            # communicate blocks while each command completes
            (output, error) = process.communicate()
            # use null instead of None
            output = output or ""
            error = error or ""
            print("Output:")
            pprint.pprint(output)
            print("Error:")
            pprint.pprint(error)

        self.assertTrue("example.invalid" in output)

if __name__ == "__main__":
    unittest.main()
