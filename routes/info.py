from flask import Blueprint, g, render_template, request, redirect, url_for, session
import urllib.parse
from api_service import APIService

info_bp = Blueprint("info", __name__, url_prefix="/info")

@info_bp.route("/")
def info():
  query = ""

  #query 파라메터를 가져온다.
  url_query = request.args.get("query")
  # 값이 없으면 session에서 가져온다.
  if query is None:
    query = session.get("query", "")
  else:
    query = url_query

  # 세션에 값이 있을경우는 파라메터 값 없을 경우는 빈값을 다시 넣는다.
  session["query"] = query
  
  print("query",query)
  squery = query.strip()
  #query
  if not query or query == "전체":
    query = "전체"
    #SearchKeyword(self, keyword, contenttypeid)
    items = APIService().SearchArea()
  else:
    if( squery.startswith("#") ) :
      tag = squery[1:].split()[0]
      # 해시태그만 있고 뒤에 내용이 없을 경우
      # 전체 검색으로 간주
      print("tag",tag)
      if tag:
        items = APIService().SearchHash(tag)
      else :
        items = []
        items = APIService().SearchArea(tag)
    else:
      items = APIService().SearchKeyword(keyword=query)
  
  return render_template("info/info.html", query=query, items = items)

@info_bp.route("/<int:info_no>")
def detail(info_no):
  item = APIService().SearchCID(info_no)
  return render_template("info/detail.html", item = item)

@info_bp.route("/festival")
def festival():
  return render_template("info/festival.html")