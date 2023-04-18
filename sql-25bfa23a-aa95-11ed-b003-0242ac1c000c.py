#!/usr/bin/env python
import sys
import ConfigParser as cp
from flask import Flask, render_template, request,redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from flaskext.mysql import MySQL
from MeetingScheduler import register as reg
from MeetingScheduler import user as usr
from MeetingScheduler import calendar

#Configuration setup
configPath = './config/mysql.config'
if len(sys.argv) == 2:
  configPath = sys.argv[1]

#Parse any external configuration options
parser = cp.ConfigParser()
parser.read(configPath)

user = parser.get('MySQLConfig', 'user')
password = parser.get('MySQLConfig', 'password')
db = parser.get('MySQLConfig', 'database')
host = parser.get('MySQLConfig', 'host')

mysql = MySQL()
app = Flask(__name__)
#Turn off autoescaping so we can inject html for xss attacks
app.config['MYSQL_DATABASE_USER'] = user
app.config['MYSQL_DATABASE_PASSWORD'] = password
app.config['MYSQL_DATABASE_DB'] = db
app.config['MYSQL_DATABASE_HOST'] = host
mysql.init_app(app)

app.secret_key = 'FKWNDJS(23/sd32!jfwedn/f,?REsdjtwed'

def isUserAuthorized():
  username, password = getUsernameAndPassword()
  response = usr.validateCredentials(username, password, mysql)
  return response

def getUsernameAndPassword():
  username = session.get('username', '')
  password = session.get('password', '')
  
  return (username, password)

@app.route("/")
def main():
  return render_template('user/login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
  if request.method == 'POST':
    #Try to register the user
    hashedPassword = generate_password_hash(request.form['password'])
    status = reg.registerUser(request.form['email'], hashedPassword, mysql)
    if status == 'Success':
      return render_template('user/register/success.html')
    else:
      return render_template('user/register/error.html', name=request.form['email'])
  else:
    #show the registration page
    return render_template('user/register/registration.html')

@app.route('/login', methods=['GET','POST'])
def login():
  if request.method == 'POST':
    response = usr.validateCredentials(request.form['username'], request.form['password'], mysql)
    if response:
      name=request.form['username']
      password= request.form['password']
      cursor = mysql.connect().cursor()
      cursor.execute('SELECT userId from Users WHERE userEmail="{0}";'.format(name))
      idNum = cursor.fetchall()
      cursor = mysql.connect().cursor()
      cursor.execute('SELECT name from Calendars WHERE userId="{0}";'.format(idNum))
      calendars = cursor.fetchall()
      session['username'] = name
      session['password'] = password
      return redirect(url_for('dashboard', calendars=calendars))
    else:
      return render_template('user/login-error.html')
  else:
    #show the login page
    return render_template('user/login.html')

@app.route("/dashboard", methods=['GET', 'POST'])
def dashboard():
  isAuthorized = isUserAuthorized()
  if not isAuthorized:
    return "Unauthorized"
  username, password = getUsernameAndPassword()
  if request.method == 'POST':
    return render_template('calendar/create/create.html')
  else:
    calendars = calendar.getCalendarList(username, mysql)
    return render_template('dashboard.html', calendars=calendars)

@app.route("/delete-calendar", methods=['GET', 'POST'])
def deleteCalendar():
  isAuthorized = isUserAuthorized()
  if not isAuthorized:
    return "Unauthorized"
  username, password = getUsernameAndPassword()
  calId = request.form['calendar']
  calendar.deleteCalendar(username, calId, mysql)
  calendars = calendar.getCalendarList(username, mysql)
  return redirect(url_for('dashboard', calendars=calendars))

@app.route('/create-calendar', methods=['GET', 'POST'])
def createCalendar():
  isAuthorized = isUserAuthorized()
  if not isAuthorized:
    return "Unauthorized"
  username, password = getUsernameAndPassword()
  if request.method == 'POST':
    #create the calendar and timeslots table for that calendar
    res, calendarId = calendar.createCalendar(request.form['calendarName'], request.form['day'], username, mysql)
    if res:
      return render_template('calendar/create/success.html', calendarId=calendarId)
    else:
      return render_template('calendar/error.html')
  else:
    #Display the create calendar page
    return render_template('calendar/create/create.html')


@app.route("/view-calendar", methods=['GET','POST'])
def viewCalendar():

  isAuthorized = isUserAuthorized()
  if not isAuthorized:
    return "Unauthorized"
  id = request.args.get('calendar')
  if id is None:
    return "Must provide a calendar id"
  username, password = getUsernameAndPassword()

  if request.method == 'GET':
    calendarDetails = calendar.getCalendarDetails(id, mysql)
    availabilityDetails = calendar.getAvailabilityForCalendar(id, mysql)
    hours = {
      "Morning Hours": [1, 2, 3,4, 5, 6, 7, 8, 9, 10, 11, 12],
      "Evening Hours": [13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24]
    }
    if calendarDetails is None:
      return "No calendar exists with that ID"
    else:
      return render_template('view-calendar.html', hours=hours, availabilityDetails=availabilityDetails, calendarId=id, calendarDetails=calendarDetails)

@app.route('/availability', methods=['GET','POST'])
def availability():

  isAuthorized = isUserAuthorized()
  if not isAuthorized:
    return "Unauthorized"

  username, password = getUsernameAndPassword()

  if request.method == 'POST':
    calendarId = request.form['calendarId']
    #update the calendar with user availability
    res = calendar.updateAvailability(username, calendarId, mysql, request.form)

    if res:
      return render_template('calendar/availability/success.html')
    else:
      return render_template('calendar/availability/error.html')
  else:
    calendarId = request.args.get('calendarId')
    #get user's current availability and display that
    res = calendar.getAvailability(username, calendarId, mysql)
    if res is not None:
      return render_template('calendar/availability/availability.html',
        calendarId=calendarId, check0=res[0],   check1=res[1],
        check2=res[2],     check3=res[3],     check4=res[4],   check5=res[5],   check6=res[6],
        check7=res[7],     check8=res[8],     check9=res[9],   check10=res[10], check11=res[11],
        check12=res[12],   check13=res[13],   check14=res[14], check15=res[15], check16=res[16],
        check17=res[17],   check18=res[18],   check19=res[19], check20=res[20], check21=res[21],
        check22=res[22],   check23=res[23])

    return render_template('calendar/availability/error.html')

if __name__ =='__main__':
  app.run()
