from flask import Blueprint, render_template, request, redirect, url_for
import urllib.parse

info_bp = Blueprint("info", __name__, url_prefix="/info")

@info_bp.route("/")
def info():
  query = request.args.get("query")
  if query:
    query = query.split()
  else:
    query = ["전체"]

  return render_template("info/info.html", query=query)

@info_bp.route("/<int:info_no>")
def detail(info_no):
  return render_template("info/detail.html",info_no = info_no)

@info_bp.route("/festival")
def festival():
  return render_template("info/festival.html")