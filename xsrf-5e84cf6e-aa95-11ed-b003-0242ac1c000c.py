from flask import Flask, render_template, jsonify, request, make_response, session, abort
from flask.ext.sqlalchemy import SQLAlchemy
from flask_mail import Message, Mail
from flask_login import LoginManager
from re import compile
import random, string
from base64 import *
from beaker.middleware import SessionMiddleware
from models import User, db

from bananas import bananas

app = Flask(__name__)


session_opts = {
    'session.type': 'file',
    'session.cookie_expires': 1800,
    'session.data_dir': '/tmp/cache/data',
    'session.lock_dir': '/tmp/cache/data',
    'session.auto': False,
}

app.wsgi_app = SessionMiddleware(app.wsgi_app, session_opts)

#import gamechange.admin
#from gamechange.decorators import *
import gamechange.error

app.config.from_envvar('FLASK_CONFIG')
db.init_app(app)
mail = Mail(app)

#login_manager = LoginManager()
#login_manager.setup_app(app)

app.register_blueprint(bananas, url_prefix="/bananas", config=app.config)

@app.route('/initDB')
def init_db():
    db.create_all()
    return "This is naughty and MUST not be in production!"

# @login_manager.user_loader
# def load_user(userid):
#     return User.get(userid)

@app.before_request
def csrf_protect():
    if request.method == "POST":
        token = session.pop('_csrf_token', None)
        if not token or token != request.form.get('_csrf_token'):
            abort(403)
        else: 
            session['_csrf_token'] = generate_csrf_token()

def generate_csrf_token():
    if '_csrf_token' not in session:
        session['_csrf_token'] = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(16))
    return session['_csrf_token']

app.jinja_env.globals['csrf_token'] = generate_csrf_token 

def hash(n):
  return ((0x0000FFFF & n)<<16) + ((0xFFFF0000 & n)>>16)

def send_email_to_user(user):
    msg = Message("Welcome to Game Change!", recipients=[user.email])
    msg.body = render_template('emails/signup.txt', email_key=urlsafe_b64encode(str(hash(user.id))), first_name=user.first_name, email_address=user.email)
    msg.html = render_template('emails/signup.html', email_key=urlsafe_b64encode(str(hash(user.id))), first_name=user.first_name, email_address=user.email)
    if not app.debug:
        mail.send(msg)
    else:
        app.logger.debug("E-mail to %s not sent, debug mode. \n %s", user.email, msg.body)  
    

@app.route("/")
def index():
    return render_template('index.html')

@app.route("/signup", methods=['POST'])
def signupFormSubmit():
    first_name = request.form.get('first_name')
    last_name = request.form.get('last_name')
    email = request.form.get('email')
    user = User(first_name,last_name,email)
    if user.isValid():
        db.session.add(user)
        db.session.commit()
        #email the user!
        send_email_to_user(user)
        return jsonify(status="200", _csrf_token=session.get('_csrf_token'))

    else:
        resp = make_response(jsonify(errors=user.error, _csrf_token=session.get('_csrf_token')), 400)
        return resp

@app.route("/email/verify/", defaults={"id_hash": None})
@app.route("/email/verify/<id_hash>")
def email_verify(id_hash):
    try:
        id = hash(int(urlsafe_b64decode(str(id_hash))))
    except (TypeError, ValueError):
        #Error, invalid hash. Tell the user to try again.
        return render_template('signup_unverified.html')

    u = User.query.get(id)
    if u != None:
        u.verified = True
        db.session.commit()
        return render_template('signup_verified.html', first_name=u.first_name, last_name=u.last_name, email=u.email)

    return render_template('signup_unverified.html')


@app.route("/email/resend", methods=['POST'])
def email_resend():
    error = dict()
    email = request.form.get('email')
    u = User.query.filter_by(email=request.form.get('email')).first()
    if '@' not in email:
        error['email'] = "Please check your e-mail address is valid."
        return make_response(jsonify(errors=error, _csrf_token=session.get('_csrf_token')), 400)
    if u:
        send_email_to_user(u)
        return jsonify(status="200", _csrf_token=session.get('_csrf_token'))
    else:
        return make_response(jsonify(errors="User not found",_csrf_token=session.get('_csrf_token')), 404)


@app.route("/email/unsubscribe/", defaults={"email": None}, methods=['GET','POST'])
@app.route("/email/unsubscribe/<email>", methods=['GET'])
def email_unsubscribe(email):
    show_form = True
    if not (request.form.get('email') == None):
        email = request.form.get('email')
        
    if email == None:
        #email address empty, so return here
        msg = 'You need to enter your email address to unsubscribe'
        pass
    else:
        results = User.query.filter_by(email=email)
        if results.count() != 1:
            #email address not found, so return here
            msg = 'The given email address was not in our system'
            pass
        else:
            show_form = False
            results.first().subscribed = False
            db.session.commit()
            msg = 'We\'ll  stop  pestering you at ' + email
    return render_template('unsubscribe.html', msg=msg, show_form = show_form)
