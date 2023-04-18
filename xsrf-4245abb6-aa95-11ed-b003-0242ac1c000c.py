"""
The `base` modules act as a parent class for request and websocket handlers, performing
common operations, setting configurations and utility methods.

.. codeauthor:: Alex Seymour <alex@luciddev.tech>
"""

import os
import functools
from pathlib import Path
from datetime import datetime
from datetime import timedelta

import jwt
import tornado.web
import tornado.websocket
from utilities import db_utils
from utilities import cron_utils

class SocketBase(tornado.websocket.WebSocketHandler):
    """
    Derives from :py:class:`tornado.websocket.WebSocketHandler`.

    :class:`.SocketBase` acts as the parent class for all websocket handlers.
    """
    def initialize(self, socket_manager):
        """
        Setup a :class:`.DatabaseManager` and :class:`.SocketManager` within
        the scope of ``self``.

        :param socket_manager: An instance of :class:`.SocketManager`
        """
        self.db_manager = db_utils.DatabaseManager(read_configuration())
        self.socket_manager = socket_manager

    def on_close(self):
        """
        Remove clients from their subscribed room(s) when their connection is
        closed.
        """
        self.socket_manager.leave(self)

    def check_origin(self, origin):
        """
        Ensures that websockets are not blocked - an issue found when trying
        to use Firefox to access the site behind Nginx.
        """
        return True

class BaseHandler(tornado.web.RequestHandler):
    """
    Derives from :py:class:`tornado.web.RequestHandler`.

    :class:`.BaseHandler` acts as the parent class for all request handlers.
    """
    tornado.web.RequestHandler.SUPPORTED_METHODS = tornado.web.RequestHandler.SUPPORTED_METHODS + ('BREW',)

    def removeslash(method):
        """
        A customised version to :py:func:`tornado.web.removeslash` which allows
        BREW as a valid HTTP method to enable the 418 easter egg.
        """
        @functools.wraps(method)
        def wrapper(self, *args, **kwargs):
            if self.request.path.endswith('/'):
                if self.request.method in ('GET', 'HEAD', 'BREW'):
                    uri = self.request.path.rstrip('/')
                    if uri:
                        self.redirect(uri, permanent=True)
                        return
                else:
                    raise tornado.web.HTTPError(404)
            return method(self, *args, **kwargs)
        return wrapper

    def initialize(self, socket_manager=None):
        """
        Sets response headers for all HTTP responses and initialises a :class:`.SocketManager`
        if one is passed in.

        :param socket_manager: An instance of :class:`.SocketManager`
        """
        self.set_header('X-Frame-Options', 'DENY')
        self.set_header('X-XSS-Protection', '1; mode=block')
        self.set_header('X-Content-Type-Options', 'nosniff')
        self.set_header('Referrer-Policy', 'same-origin')
        self.set_header('Content-Security-Policy', 'default-src \'self\' \'unsafe-inline\'; img-src \'self\' data:; script-src \'self\' \'unsafe-eval\' \'unsafe-inline\' data:; connect-src \'self\' ws:;')

        if socket_manager is not None:
            self.socket_manager = socket_manager

    @removeslash
    def prepare(self):
        """
        Setup a database session, initialise application configuration,
        handle user sessions validation and verify user access rights.
        """
        self.system_configuration = read_configuration()
        self.settings['cookie_secret'] = self.system_configuration['cookie_secret']
        self.db_manager = db_utils.DatabaseManager(self.system_configuration)
        self.cron_manager = cron_utils.CRONManager()
        self.jwt_secret = self.system_configuration['jwt_secret']
        remote = bool('/remote' in self.request.uri)
        redirect_exclusions = [
            '/',
            '/login',
            '/register',
            '/leaderboard'
        ]
        db_settings = self.db_manager.retrieve_settings()

        if db_settings is not None:
            self.system_configuration.update(db_settings)
        else:
            self.system_configuration['site_title'] = 'BUCSS CTF Framework'
            self.system_configuration['end_message'] = 'This event has now finished.'

        self.config = {
            'site_title': self.system_configuration['site_title']
        }

        if self.current_user is None and self.request.uri not in redirect_exclusions and not remote:
            self.redirect('/')
            return
        elif self.current_user is not None:
            cur_user = self.current_user
            cur_user['exp'] = datetime.utcnow() + timedelta(hours=1)
            self.config['user'] = cur_user
            self.set_secure_cookie('user', self.encode_jwt(cur_user), httponly=True)

        if '/admin' in self.request.uri:
            if not self.current_user or cur_user['role'] != 'admin':
                self.redirect('/')
                return

        if self.db_manager.get_error_state() is True:
            self.set_status(401)
            self.write('Database authentication failed.')
            self.finish()

    def get_current_user(self):
        """
        Retrieves and decrypts the JWT stored in the user cookie.
        If the JWT fails to validate the user is automatically logged out.

        :returns: dict
        """
        cookie = self.get_secure_cookie('user')
        decoded_jwt = None

        if cookie is not None:
            try:
                decoded_jwt = jwt.decode(cookie, self.jwt_secret, algorithms=['HS256'])
            except jwt.ExpiredSignatureError:
                self.redirect('/logout')
                return
            except jwt.DecodeError:
                self.redirect('/logout')
                return
        else:
            self.clear_cookie('user')

        return decoded_jwt

    def encode_jwt(self, payload):
        """
        Creates and encrypts a JWT from a dictionary.

        .. note::
            Payload should be the result of :func:`build_jwt_payload`.

        :param payload: The JWT payload.
        :type payload: dict
        """
        return jwt.encode(payload, self.jwt_secret, algorithm='HS256')

    @staticmethod
    def build_jwt_payload(user):
        """
        Builds a valid JWT payload.

        :param user: A user document retrieved from the database.
        :type user: :py:class:`pymongo.cursor.Cursor`
        """
        return {
            '_id': str(user['_id']),
            'first_name': user['first_name'],
            'last_name': user['last_name'],
            'username': user['username'],
            'role': user['role'],
            'email': user['email'],
            'iat': datetime.utcnow(),
            'exp': datetime.utcnow() + timedelta(hours=1)
        }

    def write_error(self, status_code, **kwargs):
        """
        Handle non 404 errors.
        """
        self.config['page_name'] = 'error'
        self.config['site_title'] = 'error'
        message = 'An unexpected error has occurred. Please try your request again.'

        self.render('error.html',
                    heading='Something went wrong :(',
                    config=self.config,
                    message=message)

    def check_xsrf_cookie(self):
        """
        Checks XSRF token are valid if the request comes from a valid path/method.

        XSRF checks are ignored for the BREW method so that the correct error code can be sent.
        """
        if self.request.method != 'BREW' and '/remote/' not in self.request.uri:
            tornado.web.RequestHandler.check_xsrf_cookie(self)

    def brew(self):
        """
        Returns error 418 if a request is made with the BREW method.
        """
        self.set_status(418, 'I am a teapot.')
        self.write('Error 418: I am a teapot.')

class PageNotFoundHandler(BaseHandler):
    """
    **Path:** (.*)

    Handles any requests that do not match any other route.
    """
    def prepare(self):
        """
        Inherits from :func:`BaseHandler.prepare` and sets the ``page_name``.
        """
        super().prepare()
        self.config['page_name'] = 'error'

    def get(self):
        """
        Display the ``error.html`` template customised for a 404 error.
        """
        self.set_status(404)
        message = 'The page you are looking for cannot be found.'
        self.render('error.html',
                    heading='404 Not Found',
                    config=self.config,
                    message=message)

def read_configuration():
    """
    Reads the config.conf file and returns a dictionary of the contents.

    :returns: dict
    """
    parent = str(Path(__file__).resolve().parents[1])
    path = os.path.join(parent, 'config.conf')
    config = {}

    with open(path, 'r') as conf_file:
        for line in conf_file:
            pair = line.split('=')
            config[pair[0]] = pair[1].strip()

    return config
