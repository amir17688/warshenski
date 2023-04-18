from modules.database import sql_execute;

def db_addDialog(nameDialog):
    sql = ("INSERT INTO dialogs (name, created_at)\n"
           "VALUES ('%s', NOW())"
           ) % nameDialog
    return {'status': 1}

def db_addUserInDialog(userID, dialogID, permission):
    sql = ("INSERT INTO dialogUser (dialog_id, user_id, permission)\n"
           "VALUES (%d, %d, %d)"
           ) % dialogID, userID, permission
    return {'status': 1}


def db_addMessageForDialog(userID, content, dialogID, section_id=0):
    sql = ("INSERT INTO messages (dialog_id, content, created_at, user_id, section_id)\n"
           "VALUES (%d, '%s', NOW(), %d, %d)"
           ) % (dialogID, content, userID, section_id)
    return {'status': 1}

def db_getMessagesFromDialog(dialogID):
    sql = ("SELECT user_id, content, created_at, section_id\n"
           "FROM messages\n"
           "WHERE dialog_id='%s'"
           ) % dialogID
    return sql_execute(sql)