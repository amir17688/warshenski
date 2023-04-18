import sqlalchemy
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker, scoped_session

engine = sqlalchemy.create_engine('mysql+pymysql://root:bajtastore@127.0.0.1/mydb')
Session = scoped_session(sessionmaker(bind=engine))

def select_all_apps():
	return s.execute("SELECT * FROM apps").fetchall()

def select_all_apps_from_user(user_id):
	return s.execute("SELECT * FROM apps a LEFT JOIN users_apps ua ON ua.app_id = a.id WHERE ua.user_id=?", user_id)

def select_all_devices_from_user(user_id):
	return s.execute("SELECT * FROM devices WHERE user_id=?", user_id)