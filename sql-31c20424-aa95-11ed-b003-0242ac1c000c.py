#!usr/bin/env python

"""
file descriptor

"""

__author__ = "Tadhg O'Rourke"
__date__ = "29/08/2019"

import sqlite3

# create connection to db
db = sqlite3.connect("contacts.sqlite")

# run update
update_sql = "UPDATE contacts SET email = 'test@myemail.ie' WHERE email LIKE 'test@email.com'"
update_cursor = db.cursor()
update_cursor.execute(update_sql)

# commit update
update_cursor.connection.commit()

# get count of rows affected
print(update_cursor.rowcount)

for row in db.execute("SELECT * FROM Contacts"):
    print(row)

update_cursor.close()
db.close()
