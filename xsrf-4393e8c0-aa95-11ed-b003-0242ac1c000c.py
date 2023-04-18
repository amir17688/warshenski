"""Tests for the XSRF tool."""

import datetime
import unittest

import config
import utils


class XsrfToolTests(unittest.TestCase):
    """Test cases for utils.XsrfTool."""

    TEST_NOW = datetime.datetime(2010, 1, 31, 18, 0, 0)

    def setUp(self):
        utils.set_utcnow_for_test(XsrfToolTests.TEST_NOW)

    def test_gen_and_verify_good_token(self):
        """Tests generating and verifying a good token."""
        config.set(xsrf_token_key='abcdef')
        tool = utils.XsrfTool()
        token = tool.generate_token(12345, 'test_action')
        self.assertTrue(tool.verify_token(token, 12345, 'test_action'))

    def test_rejects_invalid_token(self):
        """Tests that an invalid token is rejected."""
        config.set(xsrf_token_key='abcdef')
        tool = utils.XsrfTool()
        timestamp = utils.get_timestamp(XsrfToolTests.TEST_NOW)
        self.assertFalse(
            tool.verify_token('NotTheRightDigest/%f' % timestamp, 12345,
                              'test_action'))

    def test_rejects_expired_token(self):
        """Tests that an expired token is rejected."""
        config.set(xsrf_token_key='abcdef')
        tool = utils.XsrfTool()
        token = tool.generate_token(12345, 'test_action')
        utils.set_utcnow_for_test(XsrfToolTests.TEST_NOW +
                                  datetime.timedelta(hours=4, minutes=1))
        self.assertFalse(tool.verify_token(token, 12345, 'test_action'))

    def test_good_with_no_prior_key(self):
        """Tests a good token when a token key has to be autogenerated.

        If the config doesn't already have an XSRF token key set, the XSRF tool
        will generate one automatically.
        """
        # config seems to be shared across tests, so we have to specifically set
        # it to None.
        config.set(xsrf_token_key=None)
        tool = utils.XsrfTool()
        token = tool.generate_token(12345, 'test_action')
        self.assertTrue(tool.verify_token(token, 12345, 'test_action'))

    def test_bad_with_no_prior_key(self):
        """Tests a bad token when a token key has to be autogenerated.

        If the config doesn't already have an XSRF token key set, the XSRF tool
        will generate one automatically.
        """
        # config seems to be shared across tests, so we have to specifically set
        # it to None.
        config.set(xsrf_token_key=None)
        tool = utils.XsrfTool()
        timestamp = utils.get_timestamp(XsrfToolTests.TEST_NOW)
        self.assertFalse(
            tool.verify_token('NotTheRightDigest/%f' % timestamp, 12345,
                              'test_action'))