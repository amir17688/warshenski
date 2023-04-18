from flask import Flask, render_template, request, url_for
from flask.ext.bootstrap import Bootstrap
import stops
import wi_procedures

app = Flask(__name__)
bootstrap = Bootstrap(app)

@app.route('/')
def main():
    return render_template('main.html')

@app.route('/stop/<pr_name>', methods=['GET', 'POST'])
def stop(pr_name):
    procedure = wi_procedures.get_procedure(pr_name)
    if request.method == 'POST':
        for param in procedure.in_params:
            param.set_value(request.form[param.name])
        getattr(stops, pr_name)(procedure)
        return render_template('stop.html', procedure=procedure)
    return render_template('stop.html', procedure=procedure)

@app.errorhandler(404)
def not_found(e):
    return render_template('404.html')

if __name__ == '__main__':
	app.debug = False
	app.run(host='0.0.0.0')
