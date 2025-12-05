from flask import Flask, render_template
from flask import Flask, request, g, render_template, redirect, session
#라우터 파일
# from routes.basic import basic_bp
from routes.info import info_bp
from routes.schedule import schedule_bp
from routes.login import login_bp, api_bp
from routes.models import db
from flask_mail import Mail


app = Flask(__name__)
app.secret_key = "mocha"

# DB 설정
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


# 메일 설정
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = '너의_이메일@gmail.com'
app.config['MAIL_PASSWORD'] = '앱비밀번호'
app.config['MAIL_DEFAULT_SENDER'] = '너의_이메일@gmail.com'

mail = Mail(app)


@app.route("/", methods=["GET"])
def index():
  return render_template("index.html")

# Blueprints 등록
app.register_blueprint(info_bp)
app.register_blueprint(schedule_bp)
app.register_blueprint(login_bp)
app.register_blueprint(api_bp)

if __name__ == "__main__":
    app.run(debug=True)
#app.run(host='0.0.0.0', port=5000)