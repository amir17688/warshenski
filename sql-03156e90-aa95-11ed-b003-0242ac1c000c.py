#############################################
#				Imports 					#
#############################################

import os
from flask import Flask, render_template, request, send_from_directory, redirect, url_for, flash, abort, Response
from flask_login import LoginManager, login_required, login_user, logout_user
from flask_mysqldb import MySQL
from forms import registerForm, loginForm
from passlib.hash import sha256_crypt
from urllib.parse import urlparse, urljoin
from werkzeug.utils import secure_filename

#############################################
#				Imports 					#
#############################################

app = Flask(__name__, static_url_path='/static')

UPLOAD_FOLDER = "C:/Users/s164376/Documents/WebTechTeam/Markis/uploads" #Put your upload folder here, used by drag&drop upload
ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])

app.config['MYSQL_HOST'] = 'cs-students.nl'
app.config['MYSQL_USER'] = 'markis'
app.config['MYSQL_PASSWORD'] = 'dlSvw7noOQbiExlU'
app.config['MYSQL_DB'] = 'markis'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = 'kjdnkjfn89dbndh7cg76chb7hjhsbGHmmDDEaQc4By9VH5667HkmFxdxAjhb5Eub' # This is just something random, used for sessions

mysql = MySQL(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
login_manager.login_message = "You need to be logged in to view this page!"

#############################################
#				App routes					#
#############################################

@app.route('/')
def home():
	# Get subjects from Database
	conn = mysql.connection
	cur = conn.cursor()
	cur.execute("""SELECT subject_id, subject_name FROM subjects WHERE 1 ORDER BY subject_id ASC""")
	rv = cur.fetchall()
	return render_template('home.html', subjects=rv)

@app.route('/uploadfile', methods=["GET", "POST"])
def uploadFile():
	if request.method == "POST":
		if 'file' not in request.files:
			flash('No selected items')
			return "Err"
		file = request.files['file']
		if file.filename == '':
			flash('No file selected')
			return "Err"
		if file and allowed_file(file.filename):
			filename = secure_filename(file.filename)
			file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
			return redirect(url_for('uploaded_file',
												filename=filename))

@app.route('/uploads/<filename>')
def uploaded_file(filename):
		return send_from_directory(app.config['UPLOAD_FOLDER'],
								filename)

@app.route('/about')
@login_required
def about():
	return render_template('about.html')

@app.route("/logout")
def logout():
    logout_user()
    return Response('<p>Logged out</p>')

@app.route('/register', methods=['GET', 'POST'])
def register():
	form = registerForm(request.form)
	if request.method == 'POST' and form.validate():
		conn = mysql.connection
		cur = conn.cursor()
    
		username = form.username.data
		first_name = form.firstname.data
		last_name = form.lastname.data
		email = form.email.data
		password = sha256_crypt.hash(form.password.data)
		rv = cur.execute("""INSERT INTO users (first_name, last_name, username, password, email) VALUES (%s, %s, %s, %s, %s)""", (first_name, last_name, username, password, email ))
		conn.commit()
		if str(rv):
			return redirect(url_for('login'))

	else:
		return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
	form = loginForm(request.form)
	if request.method == 'POST' and form.validate():

		# Get the password Hash from  the DB where username
		conn = mysql.connection
		cur = conn.cursor()
		cur.execute("""SELECT id, password FROM users WHERE username="%s" """ % str(form.username.data) )
		rv = cur.fetchall()
		#return str(rv[0]['password'])
		if sha256_crypt.verify(form.password.data, str(rv[0]['password'])):
			user = User(rv[0]['id'])
			user.authenticate(form.username.data)
			login_user(user)
		else:
			return "Wrong password"

		flash('Logged in successfully.')

		next = request.args.get('next')
		if not is_safe_url(next):
			return abort(400)

		return redirect(next or url_for('home'))
	else:
		return render_template('login.html', form=form)


#############################################
#			Paths to static Files			#
#############################################

@app.route('/css/<path:filename>')
def css(filename):
	return send_from_directory('css',
                               filename)
@app.route('/js/<path:filename>')
def javascript(filename):
	return send_from_directory('js',
                               filename)

#############################################
#			   Helper Functions 			#
#############################################

@login_manager.user_loader
def load_user(userid):
    return User(userid)

def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and \
           ref_url.netloc == test_url.netloc

def allowed_file(filename):
		return '.' in filename and \
		filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

class User:
	def __init__(self, uid):
		self.is_authenticated = False
		self.is_active = False
		self.is_anonymous = True
		self.username = None
		self.user_id = uid

	def __repr__(self):
		return "%d/%s" % (self.user_id, self.username)

	def get_id(self):
		conn = mysql.connection
		cur = conn.cursor()
		cur.execute("""SELECT id FROM users WHERE username="%s" """ % self.username)
		rv = cur.fetchall()
		return str(rv[0]['id'])

	def authenticate(self, username):
		self.is_authenticated = True
		self.is_active = True
		self.is_anonymous = False
		self.username = username

	def setUsername(self, username):
		self.username = username

	def get(user_id):
		return self

	def returnUsername(self):
		return self.username

#############################################
#   Fasten your seatbelts, here we go! 		#
#############################################

if __name__ == '__main__':
	app.run(debug=True)