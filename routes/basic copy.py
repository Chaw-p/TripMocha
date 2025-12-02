from flask import Blueprint, render_template

user_bp = Blueprint("user", __name__, url_prefix="/user")

@user_bp.route("/", methods=["GET"])
def login():
  return render_template("user/login.html")