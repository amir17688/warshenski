import pymysql.cursors

class MySQLdb(object):
    def __init__(self, host, user, password, db, charset):
        self.connection = pymysql.connect(
        host= host,
        user= user,
        password= password,
        db= db,
        charset= charset,
        cursorclass=pymysql.cursors.DictCursor)

    def close_connection(self):
        self.connection.close()    

    def connect_sql(self, sql):
        """Connects to database, excutes sql, closes connection"""
        with self.connection.cursor() as cursor:
            cursor.execute(sql)
            result = cursor.fetchall()
            return(result)

    def update_sql(self, column, location_nw,title):
        #SQL UPDATE STATEMENT
        sql_update = f"UPDATE `artikelen` SET `{column}` = '{location_nw}' WHERE `title` = '{title}'" 
        print(sql_update)
        # exit()
        with self.connection.cursor() as cursor:
            cursor.execute(sql_update)
        return
