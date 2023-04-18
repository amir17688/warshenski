from flask import Blueprint, request, session, g, redirect, url_for, \
     render_template, flash

from flask_login import login_user, logout_user, current_user
from flask_security import login_required

from benwaonline.database import db
from benwaonline.oauth import twitter
from benwaonline.models import user_datastore, User
from benwaonline.auth import auth
from benwaonline.auth.forms import RegistrationForm

@auth.before_request
def before_request():
    g.user = current_user

@auth.route('/test')
def test():
    if current_user.is_authenticated:
        return str(current_user.username) + str(current_user.user_id)

    return "not logged in " + str(current_user.is_authenticated)

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.test'))

@auth.route('/login/auth')
def oauthorize():
    if g.user.is_authenticated:
        return redirect(url_for('gallery.show_posts'))
    callback_url = url_for('auth.oauthorize_callback', next=request.args.get('next'))
    return twitter.authorize(callback=callback_url or request.referrer or None)

@auth.route('/oauthorize')
def oauthorize_callback():
    resp = twitter.authorized_response()
    if not resp:
        flash(u'You denied the request to sign in.')
        return redirect(url_for('gallery.show_posts'))

    user_id = resp['user_id']
    user = User.query.filter_by(user_id=user_id).first()

    if user:
        login_user(user)
        next = request.args.get('next')
        flash('You were signed in as %s' % user.username)
        return redirect(url_for('auth.test'))

    else:
        session['user_id'] = user_id
        session['token'] = resp['oauth_token']
        session['secret'] = resp['oauth_token_secret']
        return redirect(url_for('auth.signup'))

@auth.route('/signup', methods=['GET', 'POST'])
def signup():
    form = RegistrationForm()
    if request.method == 'POST' and form.validate_on_submit():
        username = ''.join([form.adj.data, form.benwa.data, form.pos.data])
        name_exists = User.query.filter(User.username == username).all()
        if name_exists:
            flash('Username %s already in use' % username)
            return redirect(url_for('auth.signup'))

        user = user_datastore.create_user(user_id=session['user_id'], username=username)
        user.oauth_token = session.pop('token')
        user.oauth_secret = session.pop('secret')
        db.session.commit()

        login_user(user)
        next = request.args.get('next')

        flash('You were signed in as %s' % user.username)
        return redirect(url_for('auth.test'))

    flash('There was an issue with sign up, please try again')
    return render_template('signup.html', form=form)