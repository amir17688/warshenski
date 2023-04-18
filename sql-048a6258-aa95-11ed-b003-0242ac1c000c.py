"""Functions for interfacing with the SQL databases.
"""
import sqlite3 as sql
import traceback

def authenticate(username, password):
    """Authenticate a user with particular password and username.

    Args
    ----
    username : String
        The username to be validated.

    password : String
        The password to be validated.

    Returns
    -------
    response : tuple
        A 4-tuple containing all necissary response elements of form:
        (bool, int, str, str) -> (authenticated, user_id, firstname, lastname)

    TODO:
    Going to have hashed password with random salt stored in db.
    will have to hash incoming password in order be able to perform
    comparison.

    """

    con = sql.connect("./resources/users.db")

    authenticated = False

    # SQL command to be executed.
    # Check if there exists a member of users db with this username and password.
    cmd = """SELECT * FROM users
             WHERE username = ? AND password = ?;
    """

    cur = con.cursor()

    # Note: password should be randomly salted hashed.
    info = (username, password)
    cur.execute(cmd, info)

    user_info = cur.fetchone()

    # Check that this account has been found. If so return user ID.
    if user_info != None:
        authenticated = True

        user_id   = user_info[0]
        firstname = user_info[2]
        lastname  = user_info[3]
    else:
        authenticated = False

        user_id = None
        firstname = None
        lastname = None

    con.close()

    return (authenticated, user_id, firstname, lastname)

def add_user(username, firstname, lastname, bio, password):
    """Function which adds a new user to user database.

    Args
    ----
    username : String
        The username for the account to be created.
    firstname : String
        The first name of the new user.
    lastname : String
        The last name of the new user.
    bio : String
        A short biography for the account to be created.
    password : String
        The password for the account to be created.

    Returns
    -------
    added : bool
        A boolean indicating if this insertion was successful. Will
        only return False if username is already taken.

    Note
    ----
    User field in users.db has unique constraint so should not allow
    account creation where username already exists.

    In future will need to perform password hashing.
    """

    added = False
    con = sql.connect("./resources/users.db")

    cmd = """INSERT INTO users (username, firstname, lastname, bio, password)
             VALUES (?, ?, ?, ?, ?);
             """

    try:
        cur = con.cursor()

        cur.execute(cmd, (new_bio, new_password))
        con.commit()
        added = True
    except sql.OperationalError as e:
        print(''.join(traceback.format_exception(etype=type(e), value=e,
                      tb=e.__traceback__)))
        con.rollback()
        added = False
    finally:
        con.close()
        return added

def update_profile(user_id, firstname, lastname, username, password, bio):
    """Function for updating a user profile.

    Args
    ----
    user_id : int
        The username for the account to be created.
    firstname : String
        The first name of the account. Not changed if equal to none
    lastname : String
        The last name of the account. Not changed if equal to none
    username : String
        The username of the account. Not changed if equal to none
    password : String
        The password of the account. Not changed if equal to none
    bio : String
        The bio of the account. Not changed if equal to none

    Returns
    -------
    updated : bool
        Boolean indicating if update was successful.

    Note
    ----
    In future will need to make new Hash for password.

    """

    updated = False

    con = sql.connect("./resources/users.db")

    try:
        cur = con.cursor()

        """
        info = (username, firstname, lastname, bio, password)
        cur.execute(cmd, info)
        """

        if firstname != None:
            cur.execute('UPDATE users SET firstname = ? WHERE id = ? LIMIT 1;',
                        (firstname, user_id))

        if lastname != None:
            cur.execute('UPDATE users SET lastname = ? WHERE id = ? LIMIT 1;',
                        (lastname, user_id))

        if username != None:
            cur.execute('UPDATE users SET username = ? WHERE id = ? LIMIT 1;',
                        (username, user_id))

        if password != None:
            cur.execute('UPDATE users SET password = ? WHERE id = ? LIMIT 1;',
                        (password, user_id))

        if bio != None:
            cur.execute('UPDATE users SET bio = ? WHERE id = ? LIMIT 1;',
                        (bio, user_id))

        con.commit()
        updated = True
    except sql.OperationalError as e:
        print(''.join(traceback.format_exception(etype=type(e), value=e,
                      tb=e.__traceback__)))
        con.rollback()
        updated = False
    finally:
        con.close()
        return updated

def get_user_profiles():
    """Gets all user profiles, including username, first name, last name, bio and
       up to 25 posts.

    Returns
    -------
    user_profile : set
        A 6-tuple containing a success indicator as well as user profile
        information of form:
        (bool, str, str, str, str, list) -> (success, username, fistname,
                                             lastname, bio, messages)
    """

    user_con = sql.connect('./resources/users.db')

    response = False

    try:
        user_cur = user_con.cursor()

        user_cur.execute('SELECT * from user;')

        response = user_cur.fetchall();
    except sql.OperationalError as e:
        print(''.join(traceback.format_exception(etype=type(e), value=e,
                      tb=e.__traceback__)))
        user_con.rollback()
    finally:
        user_con.close()

    return response

def get_user_profile(user_id):
    """Gets a user profile, including username, first name, last name, bio and
       up to 25 posts.

    Args
    ----
    user_id : int
        Unique integer ID for a user.

    Returns
    -------
    user_profile : tuple
        A 6-tuple containing a success indicator as well as user profile
        information of form:
        (bool, str, str, str, str, list) -> (success, username, fistname,
                                             lastname, bio, messages)
    """

    user_con = sql.connect('./resources/users.db')
    message_con = sql.connect('./resources/messages.db')

    messages = []

    try:
        user_cur = user_con.cursor()
        user_cur.execute('SELECT * FROM users WHERE id = {0} LIMIT 1;'
                         .format(user_id))

        # Fetch username, first name, last name and bio for return.
        row = user_cur.fetchone()

        # Get users latest posts.
        message_cur = message_con.cursor()

        cmd = """SELECT * FROM messages
                  WHERE poster_id = {0}
                  ORDER BY timeposted
                  DESC LIMIT 25;
        """.format(user_id)

        message_cur.execute(cmd)
        unformatted_messages = message_cur.fetchall()

        # If users posts found, format for return.
        if unformatted_messages != None:
            for message in unformatted_messages:
                messages.append({
                    'content'   : message[1],
                    'likes'     : message[6],
                    'comments'  : message[7],
                    'timeposted': message[8],
                    'eventtime' : message[9]
                })
        else:
            messages = None

        # Add success indicator
        success   = True
        # Add username.
        username  = row[1]
        # Add first name.
        firstname = row[2]
        # Add last name.
        lastname  = row[3]
        # Add bio.
        bio       = row[4]
    except sql.OperationalError as e:
        print(''.join(traceback.format_exception(etype=type(e), value=e,
                      tb=e.__traceback__)))
        user_con.rollback()
        message_con.rollback()
        # Add failure indicator.
        success = False
        username = firstname = lastname = bio = None
    finally:
        user_con.close()
        message_con.close()
        return (success, username, firstname, lastname, bio, messages)

def add_message(message, timeposted, eventtime, poster_id, poster_username,
                poster_firstname, poster_lastname):
    """Function to add message to messages database.

    Args
    ----
    content - str
        The content of this message.
    timeposted - str
        The time at which this message was submitted.
    eventtime - str (optional)
        The event time for this message.
    poster_id - int
        The ID of the user posting this message.
    poster_username - str
        The username of the user posting this message.
    poster_firstname - str
        The first name of the user posting this message.
    poster_lastname - str
        The last name of the user posting this message.

    Returns
    -------
    success - bool
        Indicator that message insertion has been successful.
    """

    con = sql.connect('./resources/messages.db')

    likes = 0
    comments = ''

    if eventtime == None:
        eventtime = "NULL"

    cmd = """INSERT INTO messages (message, poster_id, poster_username,
                 poster_firstname, poster_lastname, likes, comments,
                 timeposted, eventtime)
             VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);"""

    try:
        cur = con.cursor()

        info = (message, poster_id, poster_username, poster_firstname,
                   poster_lastname, likes, comments, timeposted, eventtime)

        cur.execute(cmd, info)
        con.commit()
        success = True
    except sql.OperationalError as e:
        print(''.join(traceback.format_exception(etype=type(e), value=e,
                      tb=e.__traceback__)))
        con.rollback()
        success = False
    finally:
        con.close()
        return success

def update_message(message_id, likes, comment):
    """Function to update a message. This includes modification of the message,
       the number of likes, the eventtime and the comments

    Args
    ----
    message_id - int
        Unique message identifier.
    likes - int
        Number of likes that should be assigned to this message.
    comment - dict
        Comment object to be added to comments table.
    """

    # Initialize database connections.
    comment_con = sql.connect('./resources/comments.db')
    message_con = sql.connect('./resources/messages.db')

    # Initiailize database cursors.
    message_cur = message_con.cursor()
    comment_cur = comment_con.cursor()

    if likes is not None:
        cmd = """UPDATE messages
                 SET likes = {0}
                 WHERE id = {1};
        """.format(likes, message_id)

        # Execute update and return success indicator.
        try:
            message_cur.execute(cmd)
            message_con.commit()
        except sql.OperationalError as e:
            print(''.join(traceback.format_exception(etype=type(e), value=e,
                          tb=e.__traceback__)))
            message_con.rollback()

            message_con.close()
            comment_con.close()
            return False

    if comment is not None:
        comment_id = 0

        # Execute new comment insertion.
        try:
            # Insert new comment into database.

            # Command to insert comment into comment table.
            cmd1 = """INSERT INTO comments (poster_id, poster_username,
                                            poster_firstname, poster_lastname,
                                            comment, timeposted)
                      VALUES ("{0}", "{1}", "{2}", "{3}", "{4}", {5});
            """.format(str(comment['userId']), str(comment['username']),
                       str(comment['firstName']), str(comment['lastName']),
                       str(comment['content']), str(comment['timeposted']))

            comment_cur.execute(cmd1)
            comment_con.commit()

            comment_id = comment_cur.lastrowid
            print(comment_id)

            # Update comments list related to entry in database for this
            # message.

            # Command to get comment list from message table.
            cmd2 = """SELECT comments
                      FROM messages
                      WHERE id = {0};
            """.format(message_id)

            message_cur.execute(cmd2)
            message_con.commit()

            comments_str = message_cur.fetchone()[0]

            if comments_str == None:
                updated_comments = comment_id 
            else:
                updated_comments = "{0},{1}".format(comments_str, comment_id)

            # Command for updating comment list in message table.
            cmd3 = """UPDATE messages
                      SET comments = "{0}"
                      WHERE id = {1};
            """.format(updated_comments, message_id)

            message_cur.execute(cmd3)
            message_con.commit()
        except sql.OperationalError as e:
            print(''.join(traceback.format_exception(etype=type(e), value=e,
                          tb=e.__traceback__)))
            message_con.rollback()
            comment_con.rollback()

            message_con.close()
            comment_con.close()
            return False

    # Close database connections.
    message_con.close()
    comment_con.close()

    # Return the first page of messages.
    return get_messages(1)

def get_messages(page):
    """Function to get messages in descending order at offset 25*(page-1)
       in descending order
    Args
    ----
    page : int
        The page number i.e. the specific chunk of 25 messages to be gathered.

    Returns
    -------
    messages : list of dict
        A list of all gathered massages including content, poster (first name,
        last name, username and user id), likes, comments, time posted, event
        date (if applicable).
    """
    con = sql.connect('./resources/messages.db')
    return_obj = []

    cmd = """SELECT * FROM messages 
             ORDER BY timeposted DESC 
             LIMIT 25 OFFSET {0};
    """.format(str(25*(page-1)))

    try:
        cur = con.cursor()
        cur.execute(cmd)

        messages = cur.fetchall()

        if cur.rowcount != 0:
            for message in messages:
                return_obj.append({
                    'id'               : message[0],
                    'content'          : message[1],
                    'posterId'        : message[2],
                    'posterUsername'  : message[3],
                    'posterFirstname' : message[4],
                    'posterLastname'  : message[5],
                    'likes'            : message[6],
                    'comments'         : __get_comments(message[7]) if \
                                             message[7] is not None else None,
                    'timePosted'       : message[8],
                    'eventTime'        : message[9]
                    })
        else:
            return_obj = []
    except sql.OperationalError as e:
        print(''.join(traceback.format_exception(etype=type(e), value=e,
                      tb=e.__traceback__)))
        con.rollback()
        return_obj = {'error': 'error getting messages'}
    finally:
        con.close()
        return return_obj

def __get_comments(comments):
    """Function to collect comments from comments database using a list
       of comma-seperated unique identifier keys.

    Args
    ----
    comments : string
        String containing comma seperated unique ID's into the
        comments table.

    Returns
    -------
    comments : list of dict
        List of comments, each of which is a dict object containing

    """

    # Form list of comment ID's in SQL compatable form.
    comment_id_input = comments.replace(',', '" OR "')
    print(comment_id_input)

    con = sql.connect('./resources/comments.db')
    return_obj = []

    # Want all rows from comments table with the specified ID's.
    cmd = """ SELECT * FROM comments
              WHERE id = "{0}";
    """.format(comment_id_input)

    try:
        cur = con.cursor()
        cur.execute(cmd)

        comments = cur.fetchall()
        print(str(comments))

        # Append all comments to return object.
        if cur.rowcount() != 0:
            for comment in comments:
                return_obj.append({
                    'id'               : comment[0],
                    'posterId'        : comment[1],
                    'posterUsername'  : comment[2],
                    'posterFirstname' : comment[3],
                    'posterFastname'  : comment[4],
                    'comment'          : comment[5],
                    'timePosted'       : comment[6]
                    })
        else:
            return_obj = None
    except sql.OperationalError as e:
        print(''.join(traceback.format_exception(etype=type(e), value=e,
                      tb=e.__traceback__)))
        con.rollback()
        return_obj = {'error': 'error getting comments'}
    finally:
        con.close()
        return return_obj

def delete_users():
    """
    Function for testing purposes. Deletes all users from user table.
    """
    deleted = False
    con = sql.connect("./resources/users.db")

    # SQL command to be executed.
    cmd = """DELETE FROM users;"""

    cur = con.cursor()

    cur.execute(cmd)
    con.commit()

    deleted = True
    con.close()
    return deleted

def delete_from_messages(message, comment):
    """Function to delete from messages table.

    Accepts a message ID and comment ID as arguments.
    If no comment argument is provided then the message
    itself will be delted. Else only the comment will be
    deleted.

    Args
    ----
    message - int
        The unique ID of the message to either have its comment
        deleted or be deleted itself.
    comment - int
        The unique ID of the comment associated with the message to
        be deleted.

    Returns
    -------
    response - dict
        The first 25 messages in the database.

    """

    message_con = sql.connect("messages.db")
    comments_con = sql.connect("comments.db")

    message_cur = message_con.cursor()
    comments_cur = comments_con.cursor()

    if comments is None:
        cmd = """DELETE FROM messages
                 WHERE id = {0};
        """.format(message)

        # Execute deletion and return success indicator 
        try:
            message_cur.execute(cmd)
            message_con.commit()
        except sql.OperationalError as e:
            print(''.join(traceback.format_exception(etype=type(e), value=e,
                          tb=e.__traceback__)))
            message_con.rollback()
            return False
    else:
        try:
            # Command to get comment ID list from messages table.
            cmd1 = """SELECT comments
                      FROM messages
                      WHERE id = {0};
            """.format(message)

            message_cur.execute(cmd1)
            message_con.commit()

            # Remove from comma seperated comments list the required ID.
            comments_str = message_cur.fetchone()[0]
            comments_arr = [x.strip() for x in comments_str.split(',')]
            comments_arr.remove(comment)
            comments_str = ','.join(str(x) for x in comments_arr)

            # Command to insert updated comments ID list into messages.
            cmd2 = """UPDATE messages
                      SET comments = "{0}"
                      WHERE id = {1};
            """.format(comments_str, message)

            message_cur.execute(cmd2)
            message_con.commit()

            # Command to delete comment from comments table.
            cmd3 = """DELETE FROM comments
                      WHERE id = {0};
            """.format(comment)

            comment_cur.execute(cmd3)
            comment_con.commit()
        except sql.OperationalError as e:
            print(''.join(traceback.format_exception(etype=type(e), value=e,
                          tb=e.__traceback__)))
            comment_con.rollback()
            message_con.rollback()

            message_con.close()
            comment_con.close()

            return False
    message_con.close()
    comments_con.close()
