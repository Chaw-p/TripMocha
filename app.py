from flask import Flask, request, g, render_template, redirect, session
#라우터 파일
# from routes.basic import basic_bp
from routes.info import info_bp
from routes.schedule import schedule_bp
from routes.models import db, CityCounty

app = Flask(__name__)
app.secret_key = "mocha"

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://tripmocha:ezen@192.168.60.133/tripmocha'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

#쿼리 받아오기
@app.before_request
def get_query():
  query = session.get("query")
  g.query = query if query is not None else ""

@app.context_processor
def inject_query():
  return {"query" : g.query}

@app.route("/", methods=["GET"])
def index():
  return render_template("index.html")

@app.route("/login", methods=["GET"])
def login():
  # session["user"] = 1
  return redirect("/")

# app.register_blueprint(basic_bp)

#info
app.register_blueprint(info_bp)

#schedule
app.register_blueprint(schedule_bp)


app.run(debug=True)
#app.run(host='0.0.0.0', port=5000)