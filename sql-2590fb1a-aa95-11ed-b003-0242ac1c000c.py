#!/usr/bin/env python
from flaskext.mysql import MySQL

def registerUser(username, password, sqlHandle):
  conn = sqlHandle.connect()
  cursor = conn.cursor()

  #Check if there is a User already

  userCheckQuery = "SELECT * FROM Users WHERE userEmail = '{0}'".format(username)
  cursor.execute(userCheckQuery)
  result = cursor.fetchone()
  if result is not None:
    #We found a user already in the db
    return "Fail"
  else:
    queryString = "INSERT INTO Users (userEmail, password) VALUES('{0}', '{1}');".format(username, password)
    cursor.execute(queryString)
    conn.commit()
    return "Success"
