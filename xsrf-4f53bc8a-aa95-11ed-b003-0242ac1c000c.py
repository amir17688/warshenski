#!/usr/bin/env python
# coding=utf-8

from webapp.web import BaseHandler
from model import dbapi


class PasswordHandler(BaseHandler):

    def check_xsrf(self):
        if self.check_xsrf_cookie() == False:
            self.clear_cookies()
            return self.redirect("/")

    def check(self):
        #email = self.get_secure_cookie("email")
        sid = self.get_secure_cookie('sid')
        if not sid:
            return False
        email = self.session.get('email')
        
        user = dbapi.User()
        if email and user.get_user(email) == 0:
            profile = user.get_user_all(email)
            if profile:
                self.time = profile[4]
                self.email = email
                return True
        else:
            self.clear_cookies()
            return False

    def get(self, error=""):
        self.check()
        params = {
            'error_info': error,
            "name": self.email,
            "xsrf_token": self.xsrf_from_html()}
        body = self.wrap_html('templates/pwdchange.html', params)
        return self.write(body)

    def post(self):
        #self.check()
        if self.check() == False:
            return self.redirect("/")
        self.check_xsrf()

        oldpassword = self.get_arg('oldpassword')
        password = self.get_arg('password')
        password2 = self.get_arg('password2')
        
        user = dbapi.User()
        error = ""

        if password == password2 and user.check_user(self.email, oldpassword) != -1:
            result = user.update_password(self.email, password)
            if result != -1:
                error = "Update Password Successfully"
            else:
                error = "Update failure, try again later"
        else:
            if password != password2:
                error = "new password inconsistent"
            else:
                error = "old password incorrect"

        return self.get(error)
