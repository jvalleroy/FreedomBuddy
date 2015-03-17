"""Tests for the HTTPS controller."""

import cherrypy
import src.connectors.https.controller as controller
import sys
import unittest
from src.utilities import HTTPSConnectorInvalidCombinationError
import types
import socks
from pprint import pprint


class CherryPyTester(unittest.TestCase):
    """Verify we're running the right CherryPy version.

    If not, we'll silently get all kinds of errors, without obvious cause.

    """
    def test_right_version(self):
        """CherryPy < 3.2 hoses things silently."""

        self.assertTrue([int(x) for x in cherrypy.__version__.split(".")]
                        >= [3,2])

class AllowRequests(unittest.TestCase):
    """Only allow specified request methods."""

    def test_allow_requests_blank(self):
        """Test to ensure calling allow_requests with no default values
           is handled correctly by returning None"""
        self.assertEquals(None, controller.allow_requests())

    def test_allow_requests_invalid(self):
        """Test to ensure calling allow_requests with invalid value
           raises Exception"""
        self.assertRaises(cherrypy.HTTPError, controller.allow_requests,
                          ["TEST"])

    def test_allow_requests_not_list(self):
        """Test to ensure calling allow_requests with value converts value
           to list"""
        self.assertEquals(None, controller.allow_requests("GET"))

class AllowIPs(unittest.TestCase):
    """Only allow access from local IP address."""

    def test_allow_ips_blank(self):
        """Test to ensure calling allow_requests with no default values
           is handled correctly by returning None"""
        self.assertEquals(None, controller.allow_ips())

    def test_allow_ips_invalid(self):
        """Test to ensure calling allow_requests with invalid value
           raises Exception"""
        self.assertRaises(cherrypy.HTTPError, controller.allow_ips, "1.2.3.4")

class MonitorTest(unittest.TestCase):
    """Make testing controllers easier."""

    def command(self, command_to_use):
        """Record arguments."""

        self.command_to_use = command_to_use

    def assertInCommand(self, commands):
        """Verify that all the commands are in the command line."""

        return map(self.assertInTuple, [(x, self.command_to_use) for x in commands])

    def setUp(self):
        """Replace the actual command execution with our override."""

        controller.command = self.command

    if sys.version_info < (2, 7):
        # Add a poor man's forward compatibility.

        class ContainsError(AssertionError):
            pass

    def assertIn(self, value_a, value_b):
        """Verify that value_a is in value_b"""
        if not value_a in value_b:
            raise self.ContainsError("%s not in %s" % (value_a, value_b))

    def assertInTuple(self, a_b):
        value_a, value_b = a_b
        return self.assertIn(value_a, value_b)

class Stopper(MonitorTest):
    """Test the "HttpStop" controller."""

    def setUp(self):
        super(Stopper, self).setUp()
        self.controller = controller.HttpStop()

    def test_stop_stops(self):
        """Stop must send the "--stop" command to the cli client."""

        try:
            self.controller.post()
        except cherrypy.HTTPRedirect:
            pass

        self.assertEqual(self.command_to_use, "--stop")

    def test_stop_redirects(self):
        """Stop redirects to ``/freedombuddy`` after POSTing."""
        with self.assertRaises(cherrypy.HTTPRedirect) as context:
            self.controller.post()
        self.assertEqual(['https://127.0.0.1:8081/freedombuddy'],
                         context.exception[0])

class Listener(MonitorTest):
    """Test the "HttpListener" controller."""

    def read_request(self, *args, **kwargs):
        return "request=aRequest"

    def test_listen_listens(self):
        """Listeners must send "--request" to the cli client."""

        fakefile = lambda: None
        fakefile.read = self.read_request

        cherrypy.request.body = fakefile
        controller.HttpsListener().index()
        cherrypy.request.body = None
        self.assertInCommand(["--request aRequest"])

class Sender(MonitorTest):
    """Test the "HttpSender" controller."""

    def setUp(self):
        super(Sender, self).setUp()

    def test_proxy_default(self):
        """Ensure proxy isn't set if no values are passed."""
        sender = controller.HttpsSender()
        self.assertEqual(None, sender.proxy)

    def test_proxy_host_set(self):
        """Ensure proxy isn't set if only host is set."""
        sender = controller.HttpsSender(proxy_host="1.2.3.4")
        self.assertEqual(None, sender.proxy)

    def test_proxy_port_set(self):
        """Ensure proxy isn't set if only port is set."""
        sender = controller.HttpsSender(proxy_port="1234")
        self.assertEqual(None, sender.proxy)

    def test_proxy_port_host_set(self):
        """Ensure proxy is created correctly if host & port are set."""
        sender = controller.HttpsSender(proxy_host="1.2.3.4",
                                        proxy_port="1234")
        self.assertTrue(isinstance(sender.proxy, socks.socksocket))
        self.assertEqual("1.2.3.4", sender.proxy._socksocket__proxy[1])
        self.assertEqual(1234, sender.proxy._socksocket__proxy[2])
        self.assertEqual(2, sender.proxy._socksocket__proxy[0])

    def test_proxy_all_values_set(self):
        """Ensure proxy is created correctly if host & port & type are set."""
        sender = controller.HttpsSender(proxy_type=socks.PROXY_TYPE_HTTP,
                                        proxy_host="1.2.3.4",
                                        proxy_port="1234")
        self.assertTrue(isinstance(sender.proxy, socks.socksocket))
        self.assertEqual("1.2.3.4", sender.proxy._socksocket__proxy[1])
        self.assertEqual(1234, sender.proxy._socksocket__proxy[2])
        self.assertEqual(3, sender.proxy._socksocket__proxy[0])

class Hosting(MonitorTest):
    """Test the "HttpHosting" controller."""

    def setUp(self):
        super(Hosting, self).setUp()
        self.controller = controller.HttpHosting()
        self.controller.respond = lambda x, y: None

    def test_get(self):
        """Test to ensure calling Get is
           handled correctly by adding List action to command"""
        self.controller.get()
        self.assertInCommand(("--action list", "--hosting"))

    def test_post_blank(self):
        """Test to ensure calling Post with no default values is handled
           correctly by returning None"""
        self.assertEqual(None, self.controller.post())

    def test_post_put_set(self):
        """Test to ensure calling Post with put set and delete not set is
           handled correctly by adding Add action to command
           and user is redirected to correct URL"""
        with self.assertRaises(cherrypy.HTTPRedirect) as context:
            self.controller.post(put="a")
        self.assertEqual(['http://127.0.0.1:8080/hosting'],
                         context.exception[0])
        self.assertInCommand(("--action add", "--hosting", "--key a"))

    def test_post_delete_set(self):
        """Test to ensure calling Post with put not set and delete set is
           handled correctly by adding Remove action to command
           and user is redirected to correct URL"""
        with self.assertRaises(cherrypy.HTTPRedirect) as context:
            self.controller.post(delete="a")
        self.assertEqual(['http://127.0.0.1:8080/hosting'],
                         context.exception[0])

        self.assertInCommand(("--action remove", "--hosting", "--key a"))

    def test_post_put_delete_set(self):
        """Test to ensure calling Post with put set and delete set causes
           an Exception to be raised"""
        self.assertRaises(HTTPSConnectorInvalidCombinationError,
                          self.controller.post, put="a", delete="a")

    def test_put(self):
        """Test to ensure calling Put with put set is
           handled correctly by adding Add action to command"""
        self.controller.put("a")
        self.assertInCommand(("--action add", "--hosting", "--key a"))

    def test_delete(self):
        """Test to ensure calling Delete with delete set is
           handled correctly by adding Remove action to command"""
        self.controller.delete("a")
        self.assertInCommand(("--action remove", "--hosting", "--key a"))

class HostedClient(MonitorTest):
    """Test the "HttpHostedClient" controller."""

    def setUp(self):
        super(HostedClient, self).setUp()
        self.controller = controller.HttpHostedClient()
        self.controller.respond = lambda x, y: None

    def test_get(self):
        """Test to ensure calling Get is
           handled correctly by adding List action to command"""
        self.controller.get("a")
        self.assertInCommand(("--action list", "--hosting", "--key a"))

    def test_post_blank(self):
        """Test to ensure calling Post with no default values is handled
           correctly by returning None"""
        self.assertEqual(None, self.controller.post(client="a"))

    def test_post_put_set(self):
        """Test to ensure calling Post with put set and delete not set is
           handled correctly by adding Add action to command
           and user is redirected to correct URL"""
        with self.assertRaises(cherrypy.HTTPRedirect) as context:
            self.controller.post(client="a", put="b")
        self.assertEqual(['http://127.0.0.1:8080/hosting/a'],
                         context.exception[0])

        self.assertInCommand(("--action add", "--hosting", "--key a",
                              "--service b"))

    def test_post_delete_set(self):
        """Test to ensure calling Post with put not set and delete set is
           handled correctly by adding Remove action to command
           and user is redirected to correct URL"""
        with self.assertRaises(cherrypy.HTTPRedirect) as context:
            self.controller.post(client="a", delete="b")
        self.assertEqual(['http://127.0.0.1:8080/hosting/a'],
                         context.exception[0])

        self.assertInCommand(("--action remove", "--hosting", "--key a",
                              "--service b"))

    def test_post_put_delete_set(self):
        """Test to ensure calling Post with put set and delete set causes
           an Exception to be raised"""
        self.assertRaises(HTTPSConnectorInvalidCombinationError,
                          self.controller.post, client="a", put="a",
                          delete="a")

    def test_put(self):
        """Test to ensure calling Put with put set is
           handled correctly by adding Add action to command"""
        self.controller.put("a", "b")
        self.assertInCommand(
            ("--action add", "--hosting", "--key a", "--service b"))

    def test_delete(self):
        """Test to ensure calling Delete with delete set is
           handled correctly by adding Remove action to command"""
        self.controller.delete("a", "b")
        self.assertInCommand(
            ("--action remove", "--hosting", "--key a", "--service b"))

class HostedService(MonitorTest):
    """Test the "HttpHostedService" controller."""

    def setUp(self):
        super(HostedService, self).setUp()
        self.controller = controller.HttpHostedService()
        self.controller.respond = lambda x, y: None

    def test_get(self):
        """Test to ensure calling Get is
           handled correctly by adding List action to command"""
        self.controller.get("a", "b")
        self.assertInCommand(
            ("--action list", "--hosting", "--key a", "--service b"))

    def test_post_blank(self):
        """Test to ensure calling Post with no default values is handled
           correctly by returning None"""
        self.assertEqual(None, self.controller.post(client="a", service="b"))

    def test_post_put_set(self):
        """Test to ensure calling Post with put set and delete not set is
           handled correctly by adding Add action to command
           and user is redirected to correct URL"""
        with self.assertRaises(cherrypy.HTTPRedirect) as context:
            self.controller.post(client="a", service="b", put="c")
        self.assertEqual(['http://127.0.0.1:8080/hosting/a/b/'],
                         context.exception[0])

        self.assertInCommand(("--action add", "--hosting", "--key a",
                              "--service b", "--location c"))

    def test_post_delete_set(self):
        """Test to ensure calling Post with put not set and delete set is
           handled correctly by adding Remove action to command
           and user is redirected to correct URL"""
        with self.assertRaises(cherrypy.HTTPRedirect) as context:
            self.controller.post(client="a", service="b", delete="c")
        self.assertEqual(['http://127.0.0.1:8080/hosting/a/b/'],
                         context.exception[0])

        self.assertInCommand(("--action remove", "--hosting", "--key a",
                              "--service b", "--location c"))

    def test_post_put_delete_set(self):
        """Test to ensure calling Post with put set and delete set causes
           an Exception to be raised"""
        self.assertRaises(HTTPSConnectorInvalidCombinationError,
                          self.controller.post, client="a", service="a",
                          put="a", delete="a")

    def test_put(self):
        """Test to ensure calling Put with put set is
           handled correctly by adding Add action to command"""
        self.controller.put("a", "b", "c")
        self.assertInCommand(
            ("--action add", "--hosting", "--key a", "--service b",
             "--location c"))

    def test_delete(self):
        """Test to ensure calling Delete with delete set is
           handled correctly by adding Remove action to command"""
        self.controller.delete("a", "b", "c")
        self.assertInCommand(
            ("--action remove", "--hosting", "--key a", "--service b",
             "--location c"))

class Consuming(MonitorTest):
    """Test the "HttpConsuming" controller."""

    def setUp(self):
        super(Consuming, self).setUp()
        self.controller = controller.HttpConsuming()
        self.controller.respond = lambda x, y: None

    def test_get(self):
        """Test to ensure calling Get is
           handled correctly by adding List action to command"""
        self.controller.get()
        self.assertInCommand(("--action list", "--consuming"))

    def test_post_blank(self):
        """Test to ensure calling Post with no default values is handled
           correctly by returning None"""
        self.assertEqual(None, self.controller.post())

    def test_post_put_set(self):
        """Test to ensure calling Post with put set and delete not set is
           handled correctly by adding Add action to command
           and user is redirected to correct URL"""
        with self.assertRaises(cherrypy.HTTPRedirect) as context:
            self.controller.post(put="a")
        self.assertEqual(['http://127.0.0.1:8080/consuming'],
                         context.exception[0])
        self.assertInCommand(("--action add", "--consuming", "--key a"))

    def test_post_delete_set(self):
        """Test to ensure calling Post with put not set and delete set is
           handled correctly by adding Remove action to command
           and user is redirected to correct URL"""
        with self.assertRaises(cherrypy.HTTPRedirect) as context:
            self.controller.post(delete="a")
        self.assertEqual(['http://127.0.0.1:8080/consuming'],
                         context.exception[0])

        self.assertInCommand(("--action remove", "--consuming", "--key a"))

    def test_post_put_delete_set(self):
        """Test to ensure calling Post with put set and delete set causes
           an Exception to be raised"""
        self.assertRaises(HTTPSConnectorInvalidCombinationError,
                          self.controller.post, put="a", delete="a")

    def test_put(self):
        """Test to ensure calling Put with put set is
           handled correctly by adding Add action to command"""
        self.controller.put("a")
        self.assertInCommand(("--action add", "--consuming", "--key a"))

    def test_delete(self):
        """Test to ensure calling Delete with delete set is
           handled correctly by adding Remove action to command"""
        self.controller.delete("a")
        self.assertInCommand(("--action remove", "--consuming", "--key a"))

class ConsumedHost(MonitorTest):
    """Test the "HttpConsumedHost" controller."""

    def setUp(self):
        super(ConsumedHost, self).setUp()
        self.controller = controller.HttpConsumedHost()
        self.controller.respond = lambda x, y: None

    def test_get(self):
        """Test to ensure calling Get is
           handled correctly by adding List action to command"""
        self.controller.get("a")
        self.assertInCommand(("--action list", "--consuming", "--key a"))

    def test_post_blank(self):
        """Test to ensure calling Post with no default values is handled
           correctly by returning None"""
        self.assertEqual(None, self.controller.post(host="a"))

    def test_post_put_set(self):
        """Test to ensure calling Post with put set and delete not set is
           handled correctly by adding Add action to command
           and user is redirected to correct URL"""
        with self.assertRaises(cherrypy.HTTPRedirect) as context:
            self.controller.post(host="a", put="b")
        self.assertEqual(['http://127.0.0.1:8080/consuming/a'],
                         context.exception[0])

        self.assertInCommand(("--action add", "--consuming", "--key a",
                              "--service b"))

    def test_post_delete_set(self):
        """Test to ensure calling Post with put not set and delete set is
           handled correctly by adding Remove action to command
           and user is redirected to correct URL"""
        with self.assertRaises(cherrypy.HTTPRedirect) as context:
            self.controller.post(host="a", delete="b")
        self.assertEqual(['http://127.0.0.1:8080/consuming/a'],
                         context.exception[0])

        self.assertInCommand(("--action remove", "--consuming", "--key a",
                              "--service b"))

    def test_post_put_delete_set(self):
        """Test to ensure calling Post with put set and delete set causes
           an Exception to be raised"""
        self.assertRaises(HTTPSConnectorInvalidCombinationError,
                          self.controller.post, host="a", put="a", delete="a")

    def test_put(self):
        """Test to ensure calling Put with put set is
           handled correctly by adding Add action to command"""
        self.controller.put("a", "b")
        self.assertInCommand(
            ("--action add", "--consuming", "--key a", "--service b"))

    def test_delete(self):
        """Test to ensure calling Delete with delete set is
           handled correctly by adding Remove action to command"""
        self.controller.delete("a", "b")
        self.assertInCommand(
            ("--action remove", "--consuming", "--key a", "--service b"))

class ConsumedService(MonitorTest):
    """Test the "HttpConsumedService" controller."""

    def setUp(self):
        super(ConsumedService, self).setUp()
        self.controller = controller.HttpConsumedService()
        self.controller.respond = lambda x, y: None

    def test_get(self):
        """Test to ensure calling Get is
           handled correctly by adding List action to command"""
        self.controller.get("a", "b")
        self.assertInCommand(
            ("--action list", "--consuming", "--key a", "--service b"))

    def test_post_blank(self):
        """Test to ensure calling Post with no default values is handled
           correctly by returning None"""
        self.assertEqual(None, self.controller.post(host="a", service="b"))

    def test_post_put_set(self):
        """Test to ensure calling Post with put set and delete not set is
           handled correctly by adding Add action to command
           and user is redirected to correct URL"""
        with self.assertRaises(cherrypy.HTTPRedirect) as context:
            self.controller.post(host="a", service="b", put="c")
        self.assertEqual(['http://127.0.0.1:8080/consuming/a/b/'],
                         context.exception[0])

        self.assertInCommand(("--action add", "--consuming", "--key a",
                              "--service b", "--location c"))

    def test_post_delete_set(self):
        """Test to ensure calling Post with put not set and delete set is
           handled correctly by adding Remove action to command
           and user is redirected to correct URL"""
        with self.assertRaises(cherrypy.HTTPRedirect) as context:
            self.controller.post(host="a", service="b", delete="c")
        self.assertEqual(['http://127.0.0.1:8080/consuming/a/b/'],
                         context.exception[0])

        self.assertInCommand(("--action remove", "--consuming", "--key a",
                              "--service b", "--location c"))

    def test_post_put_delete_set(self):
        """Test to ensure calling Post with put set and delete set causes
           an Exception to be raised"""
        self.assertRaises(HTTPSConnectorInvalidCombinationError,
                          self.controller.post, host="a", service="a",
                          put="a", delete="a")

    def test_put(self):
        """Test to ensure calling Put with put set is
           handled correctly by adding Add action to command"""
        self.controller.put("a", "b", "c")
        self.assertInCommand(
            ("--action add", "--consuming", "--key a", "--service b",
             "--location c"))

    def test_delete(self):
        """Test to ensure calling Delete with delete set is
           handled correctly by adding Remove action to command"""
        self.controller.delete("a", "b", "c")
        self.assertInCommand(
            ("--action remove", "--consuming", "--key a", "--service b",
             "--location c"))

class Query(MonitorTest):
    """Test the "HttpQuery" controller."""

    def setUp(self):
        super(Query, self).setUp()
        self.controller = controller.HttpQuery()

    def test_post(self):
        """Do requests hook into the CLI client?"""

        try:
            self.controller.post("a", "b")
        except cherrypy.HTTPRedirect:
            pass
        self.assertInCommand(
            ("--query", "--key a", "--service b"))

    def test_post_redirects(self):
        """Are requests redirected appropriately?"""

        self.assertRaises(cherrypy.HTTPRedirect,
                          self.controller.post, *("a", "b"))

class MainTest(unittest.TestCase):
    """Tests the controller's main function."""

    def setUp(self):
        option_list = ("outgoing", "destination", "listen", "monitor")
        self.options = lambda: None
        self.config = controller.parse_config()

        for attr in option_list:
            setattr(self.options, attr, 0)

        # remove cherrypy logs, because they're visually distracting.
        cherrypy.log.error_log.removeHandler(cherrypy.log.error_log)
        cherrypy.log.access_log.removeHandler(cherrypy.log.access_log)

    def test_monitor_starts(self):
        """Verify starting the monitor doesn't error."""

        self.options.monitor = 1
        controller.main(self.options, start_httpserver=False, **self.config)

if __name__ == "__main__":
    unittest.main()
