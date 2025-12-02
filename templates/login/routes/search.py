from flask import Blueprint, render_template, request, redirect, url_for
import urllib.parse

search_bp = Blueprint("search", __name__, url_prefix="/search")

@search_bp.route("/")
def search():
  query = request.args.get("query")
  return render_template("search/search.html", query=query)