from flask import Flask, render_template, url_for, flash, redirect, request
from flask_sqlalchemy import SQLAlchemy 

app = Flask(__name__, static_folder='static', static_url_path='')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.sqlite3'
app.config['SECRET_KEY'] = "random string"
db = SQLAlchemy(app)

class User(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	email = db.Column(db.String(50))
	password = db.Column(db.String(20))

	def __init__(self, email, password):
		self.email = email
		self.password = password

@app.route('/')
def home():
	return render_template('home.html')

@app.route('/tables')
def tables():
	return render_template('tables.html', User=User.query.all())

@app.route('/login', methods=['GET', 'POST'])
def login():
	if request.method == 'POST':
		user = User(request.form['email'], request.form['password'])
		db.session.add(user)
		db.session.commit()
		return redirect(url_for('tables'))
	return render_template('login.html')

# Drop/Create all Tables
db.drop_all()
db.create_all()

if __name__ == '__main__':
	app.run(debug = True)
	