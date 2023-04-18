"""todo_server_db.py

A class for communicating with MySQL to add, update, and remove tags and tasks.
"""

import sys
import datetime
import MySQLdb

class Database:
    """Interface to the MySQL database.

    A class for communicating with MySQL to add, update, and remove tags and
    tasks. Changing database methods will effect network/network.py since
    the method calls are only defined there and in the actual client script
    todo.py. The global attributes here are used as responses from the Todo
    server in todo_server_thread.py.

    Attributes:
        DEFAULT_TAG: tag to default to if no default tag is specified
        CANT_CONNECT: returned when Database can't connect to MySQL
        SUCCESS: returned for successful database calls
        DUPLICATE: returned when a method attempts to insert a duplicate entry
        DOES_NOT_EXIST: returned when a delete or update method can not find the
            row to delete or update
        INVALID_DATE: returned when a date passed to a method is not valid
        DATA: returned when data is passed across the network rather than an
            enumerated reponse
    """

    DEFAULT_TAG = 'misc'
    CANT_CONNECT = 0
    SUCCESS = 1
    DUPLICATE = 2
    DOES_NOT_EXIST = 3
    INVALID_ID = 4
    INVALID_DATE = 5
    DATA = 6


    def __init__(self, default_tag):
        """Pass configuration to the database class.

        Args:
            default_tag: tag name that task creation defaults to
        """
        self.default_tag = default_tag

    def connect(self, hostname='localhost', username='todo', password='todo',
            database='todo'):
        """Connects to the MySQL database.

        Args:
            hostname: MySQL hostname
            username: MySQL username
            password: MySQL password
            database: MySQL database

        Returns:
            SUCCESS if the connection succeeded or CANT_CONNECT if the
            connection was not made.
        """
        try:
            self.__con = MySQLdb.connect(hostname, username, password, database)
            self.__con.autocommit(True)
            return Database.SUCCESS
        except MySQLdb.Error:
            return Database.CANT_CONNECT

    def close(self):
        """Close the database connection."""
        self.__con.close()

    @staticmethod
    def __format_date(date):
        """Checks a date for validity then formats it.

        Args:
            date: string to format

        Returns:
            INVALID_DATE if the date is not valid or a formatted date otherwise.
        """
        try:
            pieces = map(lambda x: int(x), date.split('-'))
            valid_date = datetime.date(pieces[2], pieces[0], pieces[1])
        except (IndexError, ValueError):
            return Database.INVALID_DATE
        return valid_date.isoformat()

    def add_tag(self, name):
        """Adds tag with name to the database.

        Args:
            name: tag name to add

        Returns:
            SUCCESS if the insertion succeeds or DUPLICATE if there is already
            a tag with name. If the cursor can not be 
        """
        cur = self.__con.cursor()
        try:
            cur.execute("INSERT INTO tags(name) VALUE('%s')" %name)
            return Database.SUCCESS
        except MySQLdb.IntegrityError:
            return Database.DUPLICATE

    def remove_tag(self, name):
        """Removes tag with name from the database along with its tasks.

        Args:
            name: tag name to be removed

        Returns:
            DOES_NOT_EXIST it no tag was removed or SUCCESS otherwise.
        """
        cur = self.__con.cursor()
        cur.execute('DELETE FROM tasks'
                " WHERE tagid=(SELECT tagid FROM tags WHERE name='%s')" %name)
        return Database.SUCCESS \
                if cur.execute("DELETE FROM tags WHERE name='%s'" %name) \
                else Database.DOES_NOT_EXIST

    def create_task(self, description, tag=None, due_date=None):
        """Creates a task and sometimes a tag to the database.

        A task with description, tag, and due_date is created. If tag does not
        exist yet, it is added to the database first. If the date is provided
        it is checked for validity before being inserted.

        Args:
            description: description of the task
            tag: name of the task's tag
            due_date: date task is due with format MM-DD-YYYY

        Returns:
            SUCCESS if the insertion succeeds, INVALID_DATE if the date is not
            valid, or DUPLICATE if a task with the same description and tag
            exists.
        """
        cols = {'description': description}
        if not tag:
            tag = self.default_tag
        if due_date:
            valid_date = Database.__format_date(due_date)
            if valid_date == Database.INVALID_DATE:
                return valid_date
            else:
                cols['due_date'] = valid_date

        cur = self.__con.cursor()
        if cur.execute("SELECT tagid FROM tags WHERE name='%s'" %tag):
            cols['tagid'] = str(cur.fetchone()[0])
        else:
            self.add_tag(tag)
            cols['tagid'] = str(self.__con.insert_id())

        try:
            cur.execute("INSERT INTO tasks(%s) VALUES('%s')"
                    %(','.join(cols.keys()), "','".join(cols.values())))
            return Database.SUCCESS
        except MySQLdb.IntegrityError:
            return Database.DUPLICATE

    def update_date(self, taskid, date=None):
        """Update the date of the task with taskid.

        Updates the date of the taskid. If date is the default of None the date
        for taskid is set to NULL.

        Args:
            taskid: id of task to update
            date: value to change due_date for taskid

        Returns:
            INVALID_DATE if the date is not valid, DOES_NOT_EXIST if no task was
            updated, or SUCCESS otherwise.
        """
        if not taskid.isdigit():
            return Database.INVALID_ID
        cur = self.__con.cursor()
        if date == None:
            date = 'NULL'
        else:
            valid_date = Database.__format_date(date)
            if valid_date == Database.INVALID_DATE:
                return valid_date
            else:
                date = "'%s'" %valid_date
        return Database.SUCCESS \
                if cur.execute("UPDATE tasks SET due_date=%s WHERE taskid=%s"
                        %(date, int(taskid))) \
                else Database.DOES_NOT_EXIST

    def complete_task(self, taskid):
        """Complete the task with taskid

        Args:
            taskid: id of task to complete
        Returns:
            DOES_NOT_EXIST if no task was updated or SUCCESS otherwise.
        """
        if not taskid.isdigit():
            return Database.INVALID_ID
        cur = self.__con.cursor()
        return Database.SUCCESS \
                if cur.execute('UPDATE tasks SET completed=TRUE'
                        ' WHERE taskid=%d' %int(taskid)) \
                else Database.DOES_NOT_EXIST

    def delete_task(self, taskid):
        """Delete the task with taskid.

        Args:
            taskid: id of the task to delete

        Returns:
            DOES_NOT_EXIST it no task was removed or SUCCESS otherwise.
        """
        if not taskid.isdigit():
            return Database.INVALID_ID
        cur = self.__con.cursor()
        return Database.SUCCESS \
                if cur.execute('DELETE FROM tasks WHERE taskid=%d' \
                %int(taskid)) else Database.DOES_NOT_EXIST

    def show(self, tag=None):
        """Gets tasks for a client to view.

        Args:
            tag: only show tasks from this tag

        Returns:
            List of dictionaries where each dictionary represents a separate
            task. Tasks are ordered by tagid then taskid.
        """
        cur = self.__con.cursor(MySQLdb.cursors.DictCursor)
        where_clause = "WHERE name='%s'" %tag if not tag == None else ''
        cur.execute('SELECT name, taskid, description, due_date, completed'
                ' FROM tasks NATURAL JOIN tags %s'
                ' ORDER BY tagid, taskid' %where_clause)
        return cur.fetchall()
