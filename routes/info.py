from flask import Blueprint, g, render_template, request, redirect, url_for, session, jsonify
import urllib.parse
from api_service import APIService

info_bp = Blueprint("info", __name__, url_prefix="/info")

@info_bp.route("/")
def info():
  #query
  query = ""
  #query 파라메터를 가져온다.
  url_query = request.args.get("query")
  # 값이 없으면 session에서 가져온다.
  if url_query is None:
    query = session.get("query", "")
  else:
    query = url_query

  # 세션에 값이 있을경우는 파라메터 값 없을 경우는 빈값을 다시 넣는다.
  session["query"] = query
  
  #type
  type = request.args.get("type")
  if type is None:
    type = "AC"
  stype = type.strip()

  #area
  area = request.args.get("area")
  if area is None:
    area = ""
  sarea = area.strip()

  #catcode
  cat = request.args.get("cat")
  if cat is None:
    cat = ""
  scat = cat.strip()
  items_list=[] 
  # 검색을 했을때 검색어 정보로 나온다.
  # 해쉬태그를 눌렀을 때 지역이면 지역값을 keyword에 타입이면 contenttypeid을 넣는다. 
  if not query or query == "전체":
    query = "전체"
    #SearchKeyword(self, keyword, contenttypeid)
    items = APIService().SearchArea(area=sarea, type =stype, cat = scat )
  else:
      # lclsSystm1_list = [ "AC", "C01", "EV", "EX", "FD", "HS", "LS", "NA", "SH", "VE" ]
    # lclsSystm1_list = ["AC", "EX", "FD", "HS", "LS", "NA", "SH", "VE" ]
    all_items = []
    
    items = APIService().SearchKeyword(keyword=query, type = stype, area = sarea, cat = scat )
    
  #아이템들이 속하는 타입값을 받아오고, 타입제목을 바꾼다.
  items_type = items.get("type")
  items["type"] = APIService().TYPE_MAPPING(items_type)

  items_list = items.get("value", [])


  return render_template("info/info.html", query=query, type = stype, cat = scat, area = sarea, items = items_list)

@info_bp.route("/<int:info_no>")
def detail(info_no):
  item = APIService().SearchCID(info_no)
  return render_template("info/detail.html", item = item)

@info_bp.route("/festival")
def festival():
  return render_template("info/festival.html")

@info_bp.route("/tourapi", methods=['GET'])
def tourapi_info():
  query = request.args.get("query", session.get("query", "전체"))
  stype = request.args.get("type", "AC").strip()
  sarea = request.args.get("area", "").strip()
  scat = request.args.get("cat", "").strip()

  page = request.args.get("page", 1, type=int)
  print(f"query={query},stype={stype},sarea={sarea},scat={scat},page={page} ")
  if not query or query == "전체":
    items_data = APIService().SearchArea(area=sarea, type =stype, cat=scat, page=page)
  else:
    items_data = APIService().SearchKeyword(keyword=query, type=stype, area=sarea, cat=scat, page=page)
    
  items_list = items_data.get("value", [])
  
  return jsonify({
    'items': items_list,
    'page': page,
    'message': f'{page}페이지 데이터를 성공적으로 로드했습니다.'
  })

@info_bp.route("/location")
def location():
  return render_template("info/add_location.html")