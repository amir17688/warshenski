from flask import Flask
from flask import redirect
from flask import url_for
from routes.topic_routes import topic_routes
from routes.auth_routes import auth_routes
from routes.reply_routes import reply_routes


app = Flask(__name__)
app.secret_key = "for test"

@app.route("/", methods=["GET"])
def index():
	return redirect(url_for("auth.login"))

app.register_blueprint(topic_routes, url_prefix="/topic")
app.register_blueprint(auth_routes, url_prefix="/auth")
app.register_blueprint(reply_routes, url_prefix="/reply")

if __name__ == "__main__":
	app.run(debug=True)