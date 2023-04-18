#!/usr/bin/env python
# coding=utf-8

import os
import hashlib
import imghdr

from webapp.web import BaseHandler
from model import dbapi

MAX_FILE_SIZE = 5000000  # upload file size setting < 5MB


class UploadHandler(BaseHandler):

    def check_xsrf(self):
        if self.check_xsrf_cookie() == False:
            return self.redirect("ftypeerror")

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
                self.id = profile[0]
                self.time = profile[4]
                self.email = email
                return True
        else:
            self.clear_cookies()
            return False

    def get_filesize(self, file):
        file.seek(0, 2)
        size = file.tell()
        file.seek(0)
        return size

    def post(self):
        self.check_xsrf() 
        if self.check() == False:
            return self.redirect("/")
        fileitem = self.request.files["filename"]
        if fileitem.filename:
            #fn = os.path.basename(fileitem.filename)
            filetype = imghdr.what(fileitem.file)
            filesize = self.get_filesize(fileitem.file)
            if filesize > MAX_FILE_SIZE:
                return self.redirect("/ftypeerror")
            if filetype is "jpeg" or filetype is "png" or filetype is "gif":
                m = hashlib.md5()
                m.update(self.email)
                email_md5 = m.hexdigest()
                path = "images/" + email_md5
                path = os.path.join(os.path.dirname(__file__), "..", path)
                open(path, "wb").write(fileitem.file.read())
                return self.redirect("/user")
            else:
                return self.redirect("/ftypeerror")
        else:
            return self.redirect("/user")
