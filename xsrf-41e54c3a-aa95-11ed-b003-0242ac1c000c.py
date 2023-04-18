"""
The ``server`` is the backbone of the BUCSS CTF Framework handling all
interactions between users and the framework.

.. codeauthor:: Alex Seymour <alex@luciddev.tech>
"""
import os
import uuid
import logging

import tornado.web
import tornado.httpserver
import tornado.ioloop
import tornado.options
from handlers import uimodules
from handlers import base
from handlers import index
from handlers import register
from handlers import login
from handlers import logout
from handlers import account
from handlers import events
from handlers import leaderboard
from handlers import sockets
from handlers import download
from handlers.admin import events as admin_events
from handlers.admin import users as admin_users
from handlers.admin import sites as admin_sites
from handlers.admin import settings as admin_settings
from handlers.admin import auth as admin_auth
from handlers.admin import leaderboards as admin_leaderboards
from handlers.admin import categories as admin_categories
from handlers.admin import challenges as admin_challenges
from handlers.admin import files as admin_files
from handlers.remote import cron
from utilities import socket_utils

class Application(tornado.web.Application):
    """
    Sets up the Tornado Web Framework :py:class:`tornado.web.Application` object.
    This class defines applications settings and routing information for HTTP requests.
    """
    def __init__(self, socket_manager):
        """
        Defines routing information for HTTP requests in the ``handlers`` list along
        with application configuration details in the ``settings`` dict.

        :param socket_manager: An instance of :py:class:`.SocketManager`
        """
        handlers = [
            (r'/', index.IndexHandler),
            (r'/register/?', register.RegisterHandler),
            (r'/login/?', login.LoginHandler),
            (r'/logout/?', logout.LogoutHandler),
            (r'/account/?', account.AccountHandler),
            (r'/events/?', events.EventListingHandler),
            (r'/events/register/(.*)/?', events.RegisterHandler, dict(socket_manager=socket_manager)),
            (r'/events/(.*)/challenges/?', events.EventHandler, dict(socket_manager=socket_manager)),
            (r'/events/(.*)/challenges/(.*)/?', events.EventHandler, dict(socket_manager=socket_manager)),
            (r'/events/(.*)/leaderboard/?', leaderboard.EventLeaderboardHandler, dict(socket_manager=socket_manager)),
            (r'/events/(.*)/leaderboard/user/(.*)/?', leaderboard.UserStatisticsHandler),
            (r'/download/(.*)/(.*)/?', download.DownloadHandler),
            (r'/leaderboard/?', leaderboard.GlobalLeaderboardHandler),
            (r'/socket/leaderboard/(.*)/?', sockets.LeaderboardSocket, dict(socket_manager=socket_manager)),
            (r'/socket/event/(.*)/?', sockets.EventSocket, dict(socket_manager=socket_manager)),
            (r'/admin/events/?', admin_events.EventsHandler),
            (r'/admin/events/edit/(.*)/?', admin_events.EditEventHandler),
            (r'/admin/events/start/(.*)&redirect=(.*)/?', admin_events.StartEventHandler, dict(socket_manager=socket_manager)),
            (r'/admin/events/stop/(.*)&redirect=(.*)/?', admin_events.StopEventHandler, dict(socket_manager=socket_manager)),
            (r'/admin/events/lock/(.*)&redirect=(.*)/?', admin_events.LockEventHandler),
            (r'/admin/events/unlock/(.*)&redirect=(.*)/?', admin_events.UnlockEventHandler),
            (r'/admin/events/answers/lock/(.*)&redirect=(.*)/?', admin_events.LockAnswersHandler),
            (r'/admin/events/answers/unlock/(.*)&redirect=(.*)/?', admin_events.UnlockAnswersHandler),
            (r'/admin/files/delete/(.*)/(.*)&redirect=(.*)/?', admin_files.DeleteHandler),
            (r'/admin/leaderboard/reset/(.*)/event/(.*)&redirect=(.*)/?', admin_leaderboards.ResetBoardHandler),
            (r'/admin/categories/delete/(.*)&redirect=(.*)/?', admin_categories.DeleteCategoryHandler),
            (r'/admin/challenges/delete/(.*)&redirect=(.*)/?', admin_challenges.DeleteChallengeHandler),
            (r'/admin/users/?', admin_users.UsersHandler),
            (r'/admin/users/approve/(.*)/?', admin_auth.ApproveUserHandler),
            (r'/admin/users/reject/(.*)/?', admin_auth.RejectUserHandler),
            (r'/admin/users/resetpassword/(.*)/?', admin_auth.ResetUserPasswordHandler),
            (r'/admin/users/lock/(.*)/?', admin_auth.LockUserHandler),
            (r'/admin/users/unlock/(.*)/?', admin_auth.UnlockUserHandler),
            (r'/admin/users/promote/(.*)/?', admin_auth.MakeUserAdminHandler),
            (r'/admin/users/demote/(.*)/?', admin_auth.RevokeUserAdminHandler),
            (r'/admin/users/delete/(.*)/?', admin_auth.DeleteUserHandler),
            (r'/admin/settings/?', admin_settings.SettingsHandler),
            (r'/admin/sites/?', admin_sites.SitesHandler),
            (r'/admin/sites/delete/(.*)/?', admin_sites.DeleteSiteHandler),
            (r'/remote/schedule/update/event/(.*)/action/(.*)/auth/(.*)/?', cron.UpdateEventHandler, dict(socket_manager=socket_manager)),
            (r'/.*/?', base.PageNotFoundHandler)
        ]

        settings = {
            'debug': False,
            'template_path': os.path.join(os.path.dirname(__file__), 'templates'),
            'static_path': os.path.join(os.path.dirname(__file__), 'static'),
            'ui_modules': uimodules,
            'cookie_secret': str(uuid.uuid4()),
            'xsrf_cookies': True
        }
        tornado.web.Application.__init__(self, handlers, **settings)

if __name__ == '__main__':
    if os.path.exists('logs/') is False:
        os.makedirs('logs/', exist_ok=True)

    tornado.options.options['log_file_prefix'] = 'logs/log.log'
    tornado.options.options['logging'] = 'warning'
    tornado.options.parse_command_line()

    socket_manager = socket_utils.SocketManager()
    app = Application(socket_manager)
    server = tornado.httpserver.HTTPServer(app)
    server.listen(8888)
    tornado.ioloop.IOLoop.instance().start()
