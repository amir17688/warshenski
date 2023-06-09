# -*- coding: utf-8 -*-
#
# Copyright © Spyder Project Contributors
# Licensed under the terms of the MIT License
# (see spyder/__init__.py for details)

"""
Manager for all LSP clients connected to the servers defined
in our Preferences.
"""

import logging
import os

from qtpy.QtCore import QObject, Slot

from spyder.config.main import CONF
from spyder.utils.misc import select_port, getcwd_or_home
from spyder.plugins.editor.lsp.client import LSPClient


logger = logging.getLogger(__name__)


class LSPManager(QObject):
    """Language Server Protocol manager."""
    STOPPED = 'stopped'
    RUNNING = 'running'

    def __init__(self, parent):
        QObject.__init__(self)
        self.main = parent

        self.lsp_plugins = {}
        self.clients = {}
        self.requests = {}
        self.register_queue = {}

        # Get configurations for all LSP servers registered through
        # our Preferences
        self.configurations_for_servers = CONF.options('lsp-server')

        # Register languages to create clients for
        for language in self.configurations_for_servers:
            self.clients[language] = {
                'status': self.STOPPED,
                'config': CONF.get('lsp-server', language),
                'instance': None
            }
            self.register_queue[language] = []

    def register_plugin_type(self, type, sig):
        self.lsp_plugins[type] = sig

    def register_file(self, language, filename, signal):
        if language in self.clients:
            language_client = self.clients[language]['instance']
            if language_client is None:
                self.register_queue[language].append((filename, signal))
            else:
                language_client.register_file(filename, signal)

    def get_root_path(self):
        """
        Get root path to pass to the LSP servers, i.e. project path or cwd.
        """
        path = None
        if self.main and self.main.projects:
            path = self.main.projects.get_active_project_path()
        if not path:
            path = getcwd_or_home()
        return path

    @Slot()
    def reinitialize_all_lsp_clients(self):
        """
        Send a new initialize message to each LSP server when the project
        path has changed so they can update the respective server root paths.
        """
        for language_client in self.clients.values():
            if language_client['status'] == self.RUNNING:
                folder = self.get_root_path()
                inst = language_client['instance']
                inst.folder = folder
                inst.initialize()

    def start_lsp_client(self, language):
        started = False
        if language in self.clients:
            language_client = self.clients[language]
            queue = self.register_queue[language]

            # Don't start LSP services in our CIs unless we demand
            # them.
            if (os.environ.get('CI', False) and
                    not os.environ.get('SPY_TEST_USE_INTROSPECTION')):
                return started

            # Start client
            started = language_client['status'] == self.RUNNING
            if language_client['status'] == self.STOPPED:
                config = language_client['config']

                if not config['external']:
                    port = select_port(default_port=config['port'])
                    config['port'] = port

                language_client['instance'] = LSPClient(
                    parent=self,
                    server_settings=config,
                    folder=self.get_root_path(),
                    language=language)

                for plugin in self.lsp_plugins:
                    language_client['instance'].register_plugin_type(
                        plugin, self.lsp_plugins[plugin])

                logger.info("Starting LSP client for {}...".format(language))
                language_client['instance'].start()
                language_client['status'] = self.RUNNING
                for entry in queue:
                    language_client.register_file(*entry)
                self.register_queue[language] = []
        return started

    def shutdown(self):
        logger.info("Shutting down LSP manager...")
        for language in self.clients:
            self.close_client(language)

    def update_server_list(self):
        for language in self.configurations_for_servers:
            config = {'status': self.STOPPED,
                      'config': CONF.get('lsp-server', language),
                      'instance': None}
            if language not in self.clients:
                self.clients[language] = config
                self.register_queue[language] = []
            else:
                logger.debug(
                    self.clients[language]['config'] != config['config'])
                current_config = self.clients[language]['config']
                new_config = config['config']
                restart_diff = ['cmd', 'args', 'host', 'port', 'external']
                restart = any([current_config[x] != new_config[x]
                               for x in restart_diff])
                if restart:
                    if self.clients[language]['status'] == self.STOPPED:
                        self.clients[language] = config
                    elif self.clients[language]['status'] == self.RUNNING:
                        self.close_client(language)
                        self.clients[language] = config
                        self.start_lsp_client(language)
                else:
                    if self.clients[language]['status'] == self.RUNNING:
                        client = self.clients[language]['instance']
                        client.send_plugin_configurations(
                            new_config['configurations'])

    def update_client_status(self, active_set):
        for language in self.clients:
            if language not in active_set:
                self.close_client(language)

    def close_client(self, language):
        if language in self.clients:
            language_client = self.clients[language]
            if language_client['status'] == self.RUNNING:
                logger.info("Stopping LSP client for {}...".format(language))
                # language_client['instance'].shutdown()
                # language_client['instance'].exit()
                language_client['instance'].stop()
            language_client['status'] = self.STOPPED

    def send_request(self, language, request, params):
        if language in self.clients:
            language_client = self.clients[language]
            if language_client['status'] == self.RUNNING:
                client = self.clients[language]['instance']
                client.perform_request(request, params)
