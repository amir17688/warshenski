from app.dbase import dbaseConn

#dbConn = dbaseConn()


class User:
    def __init__(self, uid, email, name):
        self.uid = uid
        self.email = email
        self.name = name

    @staticmethod
    def create_user(user):
        # print(user.email)
        dbConn =  dbaseConn()
        with dbConn.db.cursor() as cursor:
            # Create a new record
            try:
                sql = "INSERT INTO `User` (`uid`, `email`, `name`) VALUES (%s, %s, %s)"
                cursor.execute(sql, (user.uid, user.email, user.name))
            except KeyError:
                dbConn.db_conn_close()
                return False
        dbConn.db.commit()
        dbConn.db_conn_close()
        return True

    @staticmethod
    def get_user_by_uid(uid):
        dbConn = dbaseConn()
        
        with dbConn.db.cursor() as cursor:
            # Select user
            sql = "SELECT `uid`, `email`, `name` FROM `User` WHERE `uid`=%s"
            print(uid)
            cursor.execute(sql, (uid,))
            result = cursor.fetchone()
            print(result)

            if result is None:
                return None
              
            print(result[0])

        dbConn.db_conn_close()
        return User(*result)

    @staticmethod
    def delete_user_by_uid(user_id):
        dbcon = dbaseConn()
        # print(user_id)
        with dbcon.db.cursor() as cursor:
            # Delete user
            sql = "DELETE FROM `User` WHERE `uid`=%s"
            try:
                cursor.execute(sql, (user_id,))
                dbcon.db.commit()
            except KeyError:
                dbcon.db_conn_close()
                return False
        dbcon.db_conn_close()
        return True

    @staticmethod
    def update_user_by_username(uid, new_user_name):
        dbcon = dbaseConn()
        # print(new_user_name)
        # print(uid)
        with dbcon.db.cursor() as cursor:
            # check if user does not exist
            # validate_sql = "SELECT `uid`,`email`,`name` FROM `User` WHERE `uid`=%s"
            validate_sql = (
                "SELECT `uid`,`email`,`name` FROM `User` WHERE `uid`=" + "'" + uid + "'"
            )
            cursor.execute(validate_sql)
            result = cursor.fetchone()
            print(result)
        if result is None:
            dbcon.db_conn_close()
            return False
        try:
            with dbcon.db.cursor() as cursor:
                update_stmt = (
                    "UPDATE `User` SET `name` = "
                    + "'"
                    + new_user_name
                    + "'"
                    + " WHERE `uid` = %s"
                )
                print(update_stmt)
                cursor.execute(update_stmt, (uid,))
                dbcon.db.commit()
        except KeyError:
            dbcon.db_conn_close()
            return False
        return True

    @staticmethod
    def update_user(uid, new_email):
        # print(uid)
        # print(new_email)
        dbcon = dbaseConn()
        with dbcon.db.cursor() as cursor:
            # check if user does not exist
            validate_sql = "SELECT `uid`, `email` FROM `User` WHERE `uid`=%s"
            cursor.execute(validate_sql, (uid,))
            result = cursor.fetchone()

            if result is None:
                dbcon.db_conn_close()
                return False
            sql = (
                "UPDATE `User` SET `email` = "
                + "'"
                + new_email
                + "'"
                + " WHERE `uid` = "
                + "'"
                + uid
                + "'"
            )
            # print(sql)
            try:
                cursor.execute(sql)
                dbcon.db.commit()
            except KeyError:
                dbcon.db_conn_close()
                return False
        dbcon.db_conn_close()
        return True

    def as_object(self):
        return {"uid": self.uid, "email": self.email, "name": self.name}

    def as_json(self):
        return json.dumps(self.as_object())
