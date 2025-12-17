from flask import Blueprint, g, render_template, request, redirect, url_for, session, jsonify
import urllib.parse
from services.api_service import APIService
from .models import db, TripMain , TripDetail

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

@info_bp.route("/location/<trip_no>", method = "POST")
def update_trip_detail(trip_no): 
  data = request.get_json()
  
  # None 체크
  # trip 여부 체크
  trip = TripDetail.query.filter_by(id=trip_no).first()
  if not trip_no:
    return jsonify({"message": f"ID가 {trip_no}인 여행을 찾을 수 없습니다."}), 404
  
  # new_trip_detail로 보낸것을 가져온다.
  required_fields = ["detail_name", "address", "latitude", "longitude"]
  missing_fields = []
  
  for field in required_fields:
    # data.get(field)는 필드가 없으면 None을 반환합니다.
    # 또한, 공백 문자열("")도 비어있다고 간주합니다.
    field_value = data.get(field)
    
    # 값이 None이거나 빈 문자열이거나 (문자열인 경우) 혹은 값이 아예 없을 경우를 체크
    if field_value is None or (isinstance(field_value, str) and not field_value.strip()):
      missing_fields.append(field)

    if missing_fields:
        return (
            jsonify({
                "message": "필수 데이터가 누락되었거나 비어 있습니다.",
                "missing_fields": missing_fields
            }), 
            400 # Bad Request
        ), None
    
  # 값을 가져온다.
  detail_name = data.get("detail_name")
  address = data.get("address")
  latitude = data.get("latitude")
  longitude = data.get("longitude")
  
  # insert 실행
  new_detail = TripDetail(
    detail_name = detail_name,
    address = address,
    latitude = latitude,
    longitude = longitude
  )

  try:
    db.session.add(new_detail)
    db.session.commit()
    return jsonify({
      "message": "새로운 여행 장소가 성공적으로 생성되었습니다.",
      "trip_id": new_detail.trip_no,
      "address": new_detail.address,
      "latitude": new_detail.latitude,
      "longitude": new_detail.longitude
      }), 201

  except Exception as e:
    db.session.rollback()
    # 내부 서버 오류 응답
    return jsonify({"message": "여행 장소 생성 중 오류가 발생했습니다.", "error": str(e)}), 500


