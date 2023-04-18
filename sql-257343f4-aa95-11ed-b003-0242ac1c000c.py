#!/usr/bin/env python
import uuid

def createCalendar(calendarName, day, username, sqlHandle):
  conn = sqlHandle.connect()
  cursor = conn.cursor()

  #Create a calendar

  userCheckQuery = "SELECT userId FROM Users WHERE userEmail = '{0}'".format(username)
  cursor.execute(userCheckQuery)
  userResult = cursor.fetchone()
  if userResult is None:
    #We found a user already in the db
    return (False, None)
  else:
    #Create item in Calendars
    calendarId = str(uuid.uuid4())


    if day == "":
      day = "2000-01-01"


    queryString = "INSERT INTO Calendars (calendarId, name, day, userId) VALUES('{0}','{1}', '{2}', {3})".format(calendarId, calendarName, day, userResult[0])
    cursor.execute(queryString)
    conn.commit()

    # Create item in TimeSlots
    queryString = """INSERT INTO TimeSlots (userId, calendarId, zero, one, two, three, four, five, six, seven, eight, nine,
                  ten, eleven, twelve, thirteen, fourteen, fifteen, sixteen, seventeen, eighteen, nineteen, twenty, twentyone,
                  twentytwo, twentythree) VALUES({0},'{1}','','','','','','','','','','','','','','','','','','','','','','',
                  '','')""".format(userResult[0], calendarId)

    cursor.execute(queryString)
    conn.commit()

    return (True, calendarId)

def getCalendarList(username, sqlInstance):
  conn = sqlInstance.connect()
  cursor = conn.cursor()
  getCalendarDetails = "SELECT DISTINCT Calendars.calendarId, Calendars.name, Calendars.day FROM Users, Calendars, TimeSlots WHERE Calendars.calendarId = TimeSlots.calendarId AND (Calendars.userId = Users.userId OR TimeSlots.userId = Users.userId) AND Users.userEmail = '{0}'".format(username)
  cursor.execute(getCalendarDetails)
  result = cursor.fetchall()
  return result

def deleteCalendar(username, calendarId, sqlInstance):
  conn = sqlInstance.connect()
  cursor = conn.cursor()
  userCheckQuery = "SELECT userId FROM Users WHERE userEmail = '{0}'".format(username)
  cursor.execute(userCheckQuery)
  userResult = cursor.fetchone()
  conn.commit()
  if userResult is None:
    #We found a user already in the db
    return (False, None)
  else:	
    removeCalendar = "DELETE FROM Calendars WHERE calendarId = '{0}' AND userId = '{1}'".format(calendarId, userResult[0])
    print(removeCalendar)
    cursor.execute(removeCalendar)
    conn.commit()
    return "True"

def getCalendarDetails(id, sqlInstance):
  conn = sqlInstance.connect()
  cursor = conn.cursor()
  getCalendarDetails = "SELECT Calendars.calendarId, Calendars.name, Calendars.day, Users.userEmail  FROM Calendars, Users WHERE Calendars.userId = Users.userId AND Calendars.calendarId = '{0}'".format(id)
  cursor.execute(getCalendarDetails)
  result = cursor.fetchone()
  return result

def getCalendarDetails(id, sqlInstance):
  conn = sqlInstance.connect()
  cursor = conn.cursor()
  getCalendarDetails = "SELECT Calendars.calendarId, Calendars.name, Calendars.day, Users.userEmail  FROM Calendars, Users WHERE Calendars.userId = Users.userId AND Calendars.calendarId = '{0}'".format(id)
  cursor.execute(getCalendarDetails)
  result = cursor.fetchone()
  return result

def getAvailabilityForCalendar(calendarId, sqlInstance):
  conn = sqlInstance.connect()
  cursor = conn.cursor()
  queryString = "SELECT Users.userEmail,  TimeSlots.one, TimeSlots.two, TimeSlots.three, TimeSlots.four, TimeSlots.five, TimeSlots.six, TimeSlots.seven, TimeSlots.eight, TimeSlots.nine, TimeSlots.ten, TimeSlots.eleven, TimeSlots.twelve, TimeSlots.thirteen, TimeSlots.fourteen, TimeSlots.fifteen, TimeSlots.sixteen, TimeSlots.seventeen, TimeSlots.eighteen, TimeSlots.nineteen, TimeSlots.twenty, TimeSlots.twentyone, TimeSlots.twentytwo, TimeSlots.twentythree, TimeSlots.zero FROM TimeSlots, Users WHERE Users.userId = TimeSlots.userId AND TimeSlots.calendarId='{0}'".format(calendarId)
  cursor.execute(queryString)
  results = cursor.fetchall()
  return results

def getAvailability(username, calendarId, sqlInstance):
  conn = sqlInstance.connect()
  cursor = conn.cursor()

  userCheckQuery = "SELECT userId FROM Users WHERE userEmail = '{0}'".format(username)
  cursor.execute(userCheckQuery)
  result = cursor.fetchone()
  if result is None:
    return None
  else:
    queryString = """SELECT zero, one, two, three, four, five, six, seven, eight, nine, ten, eleven, twelve,
                  thirteen, fourteen, fifteen, sixteen, seventeen, eighteen, nineteen, twenty, twentyone,
                  twentytwo, twentythree FROM TimeSlots WHERE userID = {0} AND calendarId='{1}'""".format(result[0], calendarId)

    cursor.execute(queryString)
    result = cursor.fetchone()
    if result:
      return result
    else:
      return ('','','','','','','','','','','','','','','','','','','','','','','','')

def updateAvailability(username, calendarId, sqlInstance, timeList):
  conn = sqlInstance.connect()
  cursor = conn.cursor()

  userCheckQuery = "SELECT userId FROM Users WHERE userEmail = '{0}'".format(username)
  cursor.execute(userCheckQuery)
  userResult = cursor.fetchone()
  if userResult is None:
    return False
  else:
    timeslotQuery = "SELECT timeSlotId FROM TimeSlots WHERE calendarId = '{0}' AND userId = {1}".format(calendarId, userResult[0])
    cursor.execute(timeslotQuery)
    timeSlotResult = cursor.fetchone()
    if timeSlotResult:
      queryString = """UPDATE TimeSlots SET zero='{0}', one='{1}', two='{2}', three='{3}', four='{4}', five='{5}', six='{6}',
                  seven='{7}', eight='{8}', nine='{9}', ten='{10}', eleven='{11}', twelve='{12}', thirteen='{13}',
                  fourteen='{14}', fifteen='{15}', sixteen='{16}', seventeen='{17}', eighteen='{18}', nineteen='{19}',
                  twenty='{20}', twentyone='{21}', twentytwo='{22}', twentythree='{23}' WHERE userId = {24} AND calendarId='{25}'""".format(
                  timeList.get('0',''),timeList.get('1',''),timeList.get('2',''),timeList.get('3',''), timeList.get('4',''),
                  timeList.get('5',''),timeList.get('6',''),timeList.get('7',''),timeList.get('8',''), timeList.get('9',''),
                  timeList.get('10',''),timeList.get('11',''),timeList.get('12',''),timeList.get('13',''), timeList.get('14',''),
                  timeList.get('15',''),timeList.get('16',''),timeList.get('17',''),timeList.get('18',''), timeList.get('19',''),
                  timeList.get('20',''),timeList.get('21',''),timeList.get('22',''),timeList.get('23',''), userResult[0], calendarId)
      cursor.execute(queryString)
      conn.commit()
    else:
      queryString = """INSERT INTO TimeSlots (zero, one, two, three, four, five, six, seven, eight, nine, ten, eleven, twelve, thirteen,
                    fourteen, fifteen, sixteen, seventeen, eighteen, nineteen, twenty, twentyone, twentytwo, twentythree, userId, calendarId) VALUES ('{0}','{1}',
                    '{2}','{3}','{4}','{5}','{6}','{7}','{8}','{9}','{10}','{11}','{12}','{13}','{14}','{15}','{16}','{17}','{18}',
                    '{19}','{20}','{21}','{22}','{23}',{24},'{25}')""".format(
                    timeList.get('0',''),timeList.get('1',''),timeList.get('2',''),timeList.get('3',''), timeList.get('4',''),
                    timeList.get('5',''),timeList.get('6',''),timeList.get('7',''),timeList.get('8',''), timeList.get('9',''),
                    timeList.get('10',''),timeList.get('11',''),timeList.get('12',''),timeList.get('13',''), timeList.get('14',''),
                    timeList.get('15',''),timeList.get('16',''),timeList.get('17',''),timeList.get('18',''), timeList.get('19',''),
                    timeList.get('20',''),timeList.get('21',''),timeList.get('22',''),timeList.get('23',''), userResult[0], calendarId)
      cursor.execute(queryString)
      conn.commit()
  return True
