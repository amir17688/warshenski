#!/usr/bin/env python
from flaskext.mysql import MySQL
from werkzeug.security import generate_password_hash, check_password_hash

def validateCredentials(username, password, sqlInstance):
  conn = sqlInstance.connect()
  cursor = conn.cursor()

  #Check username and password matches in DB
  getUsernameAndPassword = "SELECT userEmail, password FROM Users WHERE userEmail = '{0}'".format(username)
  cursor.execute(getUsernameAndPassword)
  result = cursor.fetchone()
  if result is not None:
    return check_password_hash(result[1], password)

  return False
