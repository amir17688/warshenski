from flask import render_template, request, redirect, url_for
from flask_login import login_user, logout_user

from application import app, db
from application.views import render_form
from application.auth.models import User
from application.auth.forms import LoginForm, RegisterForm

@app.route("/auth/login", methods = ["GET", "POST"])
def auth_login():
    if request.method == "GET":
        return render_login()
    form = LoginForm(request.form)
    if not form.validate():
        return render_loginForm(form)

    user = User.query.filter_by(username=form.username.data, password=form.password.data).first()
    if not user:
        return render_loginInvalid(form)

    login_user(user)
    return redirect(url_for("index"))

@app.route("/auth/logout")
def auth_logout():
    logout_user()
    return redirect(url_for("index"))


@app.route("/auth/register")
def auth_register():
    return render_register()

@app.route("/auth/register/", methods=["POST"])
def auth_user_create():
    form = RegisterForm(request.form)
	
    if not form.validate():
        return render_registerForm(form)

    u = User(form.username.data, form.password.data)    

    db.session().add(u)
    db.session.commit()
    
    login_user(u)
  
    return redirect(url_for("index"))

def render_login():
    return render_loginForm(LoginForm())

def render_loginForm(form):
    return render_form(form, False, url_for("auth_login"), "Login", "", True, "")

def render_loginInvalid(form):
    return render_form(form, True, url_for("auth_login"), "Login", "Invalid username or password.")

def render_register():
    return render_registerForm(RegisterForm())

def render_registerForm(form):
    return render_form(form, False, url_for("auth_user_create"), "Register", "", True, "")
