from flask import Flask, render_template, request, g, redirect, session
from routes.info import info_bp
from routes.schedule import schedule_bp
from routes.login import login_bp, api_bp
from routes.models import db
import pymysql

app = Flask(__name__)
app.secret_key = "mocha"



@app.teardown_appcontext
def close_db(exception):
    db_conn = g.pop("db", None)
    if db_conn is not None:
        db_conn.close()

# -------------------------------------------------
# SQLAlchemy 설정
# -------------------------------------------------
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://tripmocha:ezen@192.168.60.133/tripmocha'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# -------------------------------------------------
# BEFORE REQUEST
# -------------------------------------------------
@app.before_request
def get_query():
    session_query = session.get("query")
    g.query = session_query if session_query is not None else ""

@app.context_processor
def inject_query():
    return {"query": g.query}

# -------------------------------------------------
# ROUTES
# -------------------------------------------------
@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

# -------------------------------------------------
# BLUEPRINTS
# -------------------------------------------------
app.register_blueprint(info_bp)
app.register_blueprint(schedule_bp)
app.register_blueprint(login_bp)
app.register_blueprint(api_bp)

# -------------------------------------------------
# RUN SERVER
# -------------------------------------------------
if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)
