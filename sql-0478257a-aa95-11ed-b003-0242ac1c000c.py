"""A basic Flask app which we can build off of.

Handles basic http requests in a simple way.
Only throws 404 errors for now.

Note: Pretty much everything should be changed.
      Also see about adding arguments to the requests.
      Should also change the names of the classes.

      The classes may not need all of these methods.
"""

from flask import Flask, jsonify, request
from flask_restful import Resource, Api
from flask_cors import CORS
import db_interac
import utils

app = Flask(__name__)
api = Api(app)
CORS(app)

# Will have to define parser objects for parsing these requests...

# Method stubs for retrieving and updating profile information.
class Profiles(Resource):
    def get(self):
        """Retreives a user profile.

        Form Elements
        -------------
        userId : int
            An integer which uniquely identifies this user.

        Returns
        -------
        JSON object containing the users first name, last name, bio and
        up to 25 of thier post recent posts.
        Note
        ----
        Need to do form argument input validation.
        """

        """
        # Check the request comes from appropriate location.
        if not utils.validate_ip(request.remote_addr)
            return {}, 403
        """

        user_id = request.form.get('userId')

        # Case where all user profiles are requested.
        if user_id is None:
            users = db_interac.get_user_profiles()

            # If profile request fails.
            if not users:
                return {}, 500

            response_obj = []

            # Build return object.
            for user in users:
                response_obj.append({
                    'id': user[0],
                    'username': user[1],
                    'firstName': user[2],
                    'lastName': user[3],
                    'bio': user[4]
                })

            return response_obj, 200

        # If specific user profile is requested.
        user_profile = db_interac.get_user_profile(user_id)
        return_obj = {}

        # Check if account creation was successful. If so
        # build return object.
        if (user_profile[0] == False):
            return_obj['error'] = 'error adding profile'
        else:
            return_obj['username']  = user_profile[1]
            return_obj['firstName'] = user_profile[2]
            return_obj['lastName']  = user_profile[3]
            return_obj['bio']       = user_profile[4]
            return_obj['messages']  = user_profile[5]

        return return_obj, 200

    def post(self):
        """Creates a new user profile.

        JSON Properties
        ---------------
        username : String
            A unique username which identifies this specific user.
        firstName : String
            The first name of the new user.
        lastName : String
            The last name of the new user.
        password : String
            A password for securty puposes.
        bio : String
            A short personal biography which the user may write.
        institutionCode : String
            A private security code used to confirm that user is a
            Northwood resident.

        Returns
        -------
        A JSON object containing success indicator.
        Note
        ----
        Need to do form argument input validation.
        """

        """
        # Check the request comes from appropriate location.
        if not utils.validate_ip(request.remote_addr)
            return {}, 403
        """

        INSTITUTION_CODE = 'northwood'

        username = request.json.get('username')
        firstname = request.json.get('firstName')
        lastname = request.json.get('lastName')
        password = request.json.get('password')
        bio = request.json.get('bio')
        institution_code = request.json.get('institutionCode')

        if institution_code != INSTITUTION_CODE:
            return {'response': 'incorrect institution code'}, 400

        # Username, first name, and last name must be alphanumeric.
        if not(username.isalnum() or firstname.isalnum() or lastname.isalnum()):
            return {'response': 'incorrect'}, 400

        # Add user profile.
        posted = db_interac.add_user(username, firstname, lastname, bio,
                                     password)

        if posted:
            # Get all current user profiles.
            result = db_interac.get_user_profiles()

            if not result:
                return {}, 500

            response_obj = []

            # Construct return object.
            for user in result:
                response_obj.append({
                    'id': user[0],
                    'username': user[1],
                    'firstName': user[2],
                    'lastName': user[3],
                    'bio': user[4]
                })

            return response_obj, 201
        else:
            return {}, 500

    def put(self):
        """Updates a user profile.

        Form Elements
        -------------
        userId : int
            An integer which uniquely identifies this user.
        firstName : string
            Specified change in firstName. If null, no change is made.
        lastName  : string
            Specified change in lastName. If null, no change is made.
        username : string
            Specified change in username. If null, no change is made.
        password : string
            Specified change in password. If null, no change is made.
        bio : string
            Specified change in bio. If null, no change is made.

        Returns
        -------
        JSON object indicating success
        Note
        ----
        Need to do form argument input validation.
        """

        """
        # Check the request comes from appropriate location.
        if not utils.validate_ip(request.remote_addr)
            return {}, 403
        """

        return_obj = False

        user_id   = request.form.get('userId')
        firstname = request.form.get('firstName')
        lastname  = request.form.get('lastName')
        username  = request.form.get('username')
        password  = request.form.get('password')
        bio       = request.form.get('bio')

        print(user_id)
        print(firstname)
        print(lastname)

        """
        Need to work around nonetype and isalnum()

        if fistname == None:
            temp1 = ""
        if lastname == None:
            temp2 = ""
        if username == None:
            temp3 = ""

        Then check if temp 1, 2 or 3 are alphanumeric
        """

        if not (firstname.isalnum() and lastname.isalnum() \
                and username.isalnum()):
            return {'response': False}, 400

        updated = db_interac.update_profile(user_id, firstname, lastname,
                                            username, password, bio)

        return {'response': updated}, 200 if updated else 400

    # method for deleting all profiles.
    def delete(self):
        deleted = db_interac.delete_users()
        return {}, 204

# Method stubs for retrieving and updating messages.
class Messages(Resource):
    # method
    # (maybe a argument for the number of messages?)

    def get(self):
        """Method to return messages in reverse chronological order.

        Form Arguments
        --------------
        page : int
            The 'page' of messages to be returned. Each page is a chunk of up to
            25 messages in reverse chronilogical order.

        Returns
        -------
        messages : list of dict
            A list containing all messages returned in this query.
        Note
        ----
        Need to do form argument input validation.
        """

        """
        # Check the request comes from appropriate location.
        if not utils.validate_ip(request.remote_addr)
            return {}, 403
        """

        page = int(request.args.get('page'))

        response = db_interac.get_messages(page)
        return response, 200

    def post(self):
        """Creates a new message.

        Form Arguments
        --------------
        content - str
            The content of this message.
        timePosted - str
            The time at which this message was submitted.
        eventTime - str (optional)
            The event time for this message.
        userId - int
            The ID of the user posting this message.
        username - str
            The username of the user posting this message.
        firstName - str
            The first name of the user posting this message.
        lastName - str
            The last name of the user posting this message.

        Returns
        -------
        response - JSON object indicating success.

        Note
        ----
        Need to do form argument input validation.
        """

        """
        # Check the request comes from appropriate location.
        if not utils.validate_ip(request.remote_addr)
            return {}, 403
        """

        message          = request.form.get('content')
        timeposted       = request.form.get('timePosted')
        eventtime        = request.form.get('eventTime')
        poster_id        = request.form.get('userId')
        poster_username  = request.form.get('username')
        poster_firstname = request.form.get('firstName')
        poster_lastname  = request.form.get('lastName')

        response = db_interac.add_message(message, timeposted, eventtime,
            poster_id, poster_username, poster_firstname, poster_lastname)


        # If message was successfully inserted, gather the first 25 messages.
        if response:
            response = db_interac.get_messages(1)
            return response, 201
        else:
            return {'response' : response}, 500

    def put(self):
        """Updates a message.

        Form Arguments
        --------------
        id - string
            The unique identifier for this particular message.
        likes - int
            The number of likes assigned to this comment. If null no new likes
            will be added.
        comment - dict
            New comment to be added to this message. Comment dict must
            contain the keys:
                content   : String containing comment text.
                userId    : Integer representing unique ID of commenter.
                username  : String containing username of commenter.
                firstName : First name of commenter.
                lastName  : Last name of commenter.
                timeposted: Timestamp for when this comment was posted.
            If null, then a new comment will not be created.

        Returns
        -------
        response - dict
            The first 25 messages in the database if successful. Otherwise
            returns error code.
        """

        """
        # Check the request comes from appropriate location.
        if not utils.validate_ip(request.remote_addr)
            return {}, 403
        """

        message_id       = request.json.get('id')
        likes            = request.json.get('likes')
        comment          = request.json.get('comment')
        print(message_id)
        print(likes)
        print(str(comment))

        # If new comment is being added, check that it has required keys.
        if comment is not None:
            if {'content', 'userId', 'username', 'firstname', 'lastname',\
                 'timeposted'}.issubset(comment):
                 return {'response': False}, 400

        response = db_interac.update_message(message_id, likes, comment)

        if response == False:
            return {'response': response}, 400

        return {'response': response}, 200

    def delete(self):
        """Deletes a message or a comment from that message.

        Form Arguments
        --------------
        message - int
            The ID of a message to be deleted in the messages table. If comment
            is provided then the message will not be deleted and only the comment
            will be.
        comment - int
            Indicates a comment which is associated with the message which
            will be deleted. If null then the message will be deleted.

        Returns
        -------
        response - dict
            The first 25 messsages in the database.
        """

        reponse = delete_from_messages(message, comment)

        return {}, 204

class Auth(Resource):
    def get(self):
        """Authenticates a users identity.

        Form Elements
        -------------
        username : String
            A unique username which identifies this specific user.
        password : String
            A password for securty puposes.

        Returns
        -------
        userId : int
            A unique integer code which identifies this user.
        firstName : string
            The first name of this user.
        lastName : string
            The last name of this user.
        Note
        ----
        Need to do form argument input validation.
        """

        """
        # Check the request comes from appropriate location.
        if not utils.validate_ip(request.remote_addr)
            return {}, 403
        """

        username = request.args.get('username')
        password = request.args.get('password')

        if username.isalnum():
            # Authenticate that user exists and has correct information.
            response = db_interac.authenticate(username, password)
            return_obj = {}

            # If first element of response tuple is not False, create
            # and return response object.
            if not response[0]:
                return_obj['error'] = 'user could not be authenticated'
                return return_obj, 401
            else:
                return_obj['userId']   = response[1]
                return_obj['firstName'] = response[2]
                return_obj['lastName']  = response[3]
                return return_obj, 200
        else:
            # Username must be alphnumeric, if not throw error.
            return_obj['error'] = 'username must be alphanumeric'
            return_obj['userId']   = None
            return_obj['firstName'] = None
            return_obj['lastName']  = None
            return return_obj, 401

api.add_resource(Profiles, '/profiles')       # route 1
api.add_resource(Messages, '/messages')       # route 2
api.add_resource(Auth, '/auth')               # route 3

if __name__ == '__main__':
    app.run(debug=True)
