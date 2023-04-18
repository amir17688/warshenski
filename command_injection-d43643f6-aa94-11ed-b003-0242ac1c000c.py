from flask import render_template, redirect, url_for, request, flash, abort,\
                    Markup, send_from_directory
from app import app, fbdb
from .forms import ProcessingForm, FILE_MAP
from . import utils
from shutil import copyfile, rmtree
import os
import tempfile
import requests
import subprocess as sub

@app.route('/')
@app.route('/about')
def index():
    return render_template('index.html',
                            title="GenSET")

@app.route('/experiment', methods=['GET'])
def experiment():
    form = ProcessingForm(request.form)
    return render_template('experiment/index.html',
                            title="Try it Out!",
                            sitekey=app.config['G_CAPTCHA_SITEKEY'],
                            form=form,
                            files=utils.SAMPLE_FILES)

@app.route('/upload', methods=['POST'])
def upload():
    # Check Google reCAPTCHA v2
    data = {
        'secret': app.config['G_CAPTCHA_SECRET'],
        'response': request.form['g-recaptcha-response'],
        'remoteip': request.remote_addr
    }
    resp = requests.post(app.config['G_CAPTCHA_VERIFY'],
                        data=data).json()

    # Check to see if user is a bot
    if resp['success']:
        # Check to see if it is a valid submission
        form = ProcessingForm()
        if not form.validate_on_submit():
            # Invalid submissions get flashed
            for field, errors in form.errors.items():
                for e in errors:
                    flash('Error in %s: %s' % (getattr(form, field).label.text, e))
        else:
            path = tempfile.mkdtemp(dir=app.config['UPLOAD_FOLDER'], prefix='')
            session_id = os.path.basename(path)

            # Save the files
            request.files['testcsv'].save(os.path.join(path, app.config['TESTING_FN']))

            if request.files['trainingcsv'].filename != '':
                request.files['trainingcsv'].save(os.path.join(path, app.config['TRAINING_FN']))
            else:
                try:
                    fn = FILE_MAP[request.form['trainingset']]
                    copyfile(os.path.join(app.config['TRAINING_FOLDER'], fn),
                             os.path.join(path, app.config['TRAINING_FN']))
                except KeyError:
                    flash('Error: \'%s\' is not supported' % request.form['trainingset'])

            # Be flashy
            link = '<a href="%s" class="alert-link">page</a>' % url_for('view', sid=session_id)
            success_txt = 'Success! To view progress later, bookmark the %s' % link
            flash(Markup(success_txt))

            # If the path exists, render the view
            f = open(os.path.join(path, 'logs.txt'), 'w')
            env = os.environ.copy()
            env['API_KEY'] = app.config['API_KEY']
            sub.Popen(['python', 'scripts/master.py', session_id, request.form['trainingset']],
                        stdout=f, stderr=f, env=env)
            return redirect(url_for('view', sid=session_id))
    else:
        # Show all authentication errors
        flash('Error: %s' % ', '.join(resp['error-codes']))

    return redirect(url_for('experiment',
                            title="Try it Out!",
                            sitekey=app.config['G_CAPTCHA_SITEKEY'],
                            form=form,
                            files=utils.SAMPLE_FILES))

@app.route('/view/<sid>')
def view(sid):
    if '/' not in sid:
        path = os.path.join(app.config['UPLOAD_FOLDER'], sid)
        if os.path.isdir(path):
            using_firebase = 'true' if app.config['FIREBASE'] else 'false'
            return render_template('view.html',
            sid=sid, title="Progress for %s" % sid, using_firebase=using_firebase)
        else:
            abort(404)
    else:
        abort(403)

@app.route('/api/script_update', methods=['POST'])
def script_update():
    if not app.config['FIREBASE']:
        abort(400)
    if request.json is None:
        abort(400)
    if request.json['auth_token'] != app.config['API_KEY']:
        abort(403)

    try:
        sid = request.json['session_id']
        progress = int(request.json['progress'])
        text = request.json['text']
    except ValueError:
        # If progress isn't an int, or if any of the fields are missing, abort.
        abort(400)

    # Actually upload the data
    data = { "progress": progress, "text": text }
    fbdb.child('sessions').child(sid).set(data)
    return '', 200

@app.route('/api/uploads/<sid>/logs')
def get_logs(sid):
    if '/' not in sid:
        path = os.path.join(app.config['UPLOAD_FOLDER'], sid)
        if os.path.isfile(os.path.join(path, app.config['LOG_FILE'])):
            return send_from_directory(directory=path,
                                        filename=app.config['LOG_FILE'])
        else:
            abort(404)
    else:
        abort(403)

@app.route('/api/uploads/<sid>/download')
def download(sid):
    if not utils.sid_is_valid(sid):
        abort(400)

    path = os.path.join(app.config['UPLOAD_FOLDER'], sid)

    if os.path.isfile(os.path.join(path, app.config['RESULTS_ZIP'])):
        return send_from_directory(directory=path,
                                    filename=app.config['RESULTS_ZIP'])
    else:
        abort(404)

@app.route('/api/uploads/<sid>', methods=['DELETE'])
def delete_upload(sid):
    if not utils.sid_is_valid(sid):
        abort(400)

    # Remove the entire upload
    path = os.path.join(app.config['UPLOAD_FOLDER'], sid)

    # If it exists, of course
    if os.path.isdir(path):
        if not app.config['TESTING']:
            rmtree(path)
    else:
        abort(404)

    # Remove from firebase
    if app.config['FIREBASE']:
        fbdb.child('sessions').child(sid).remove()

    flash('Success! Deleted run data for "%s"' % sid)
    return '', 200
