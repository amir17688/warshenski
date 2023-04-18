from flask import Blueprint, request, session, g, redirect, url_for, \
     render_template, flash, current_app

bp = Blueprint('benwaonline', __name__)

@bp.route('/')
def under_construction():
    # return redirect(url_for('gallery.show_posts'))
    return redirect(url_for('auth.test'))
