from flask import Flask, render_template, request, url_for
from flask.ext.bootstrap import Bootstrap
import stops
import wi_procedures

app = Flask(__name__)
bootstrap = Bootstrap(app)

BAD_WORDS = ['select', 'drop', 'delete', '\'', ';', '--']

@app.route('/')
def main():
    return render_template('main.html')

@app.route('/stop/<pr_name>', methods=['GET', 'POST'])
def stop(pr_name):
    procedure = wi_procedures.get_procedure(pr_name)
    if request.method == 'POST':
        sql_injection = False
        for param in procedure.in_params:
            if sql_injection:
                break
            value = request.form[param.name]
            print(value)
            for bw in BAD_WORDS:
                if bw in value:
                    param.set_value('please no \'%s\'' % bw)
                    sql_injection = True
                    break
            if not sql_injection:
                param.set_value(value)
        if not sql_injection:
            getattr(stops, pr_name)(procedure)
        return render_template('stop.html', procedure=procedure)
    return render_template('stop.html', procedure=procedure)

@app.errorhandler(404)
def not_found(e):
    return render_template('404.html')

if __name__ == '__main__':
	app.debug = False
	app.run(host='0.0.0.0')
