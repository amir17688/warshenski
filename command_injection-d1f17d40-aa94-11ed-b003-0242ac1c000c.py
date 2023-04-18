from mysql_commands import *

def select_all_apps():
	return select_row_from_mysql_command("SELECT * FROM apps")

def select_all_apps_from_user(user_id):
	return select_row_from_mysql_command("SELECT * FROM apps a LEFT JOIN users_apps ua ON ua.app_id = a.id WHERE ua.user_id=?", user_id)

def select_all_devices_from_user(user_id):
	return select_row_from_mysql_command("SELECT * FROM devices WHERE user_id=?", user_id)