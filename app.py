from flask import Flask, render_template, request, g, redirect, session
from routes.info import info_bp
from routes.schedule import schedule_bp
from routes.login import login_bp, api_bp
from routes.models import db

app = Flask(__name__)
app.secret_key = "mocha"

# DB 설정
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://tripmocha:ezen@192.168.60.133/tripmocha'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# 쿼리 받아오기
@app.before_request
def get_query():
    query = session.get("query")
    g.query = query if query is not None else ""

@app.context_processor
def inject_query():
    return {"query": g.query}


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


# Blueprints 등록
app.register_blueprint(info_bp)
app.register_blueprint(schedule_bp)
app.register_blueprint(login_bp)
app.register_blueprint(api_bp)

if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)
