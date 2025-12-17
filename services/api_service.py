
import requests
import json
from dotenv import load_dotenv
import os
from .models import db, TripMain , TripMapping 
# pip install python-dotenv

load_dotenv()

class APIService :
  # 맨앞의 "#"여부로 key 검색인지 hash 검색인지 구별한다
  # keyword 검색 : SearchData(self,keyword)
  # Hash로 검색 : SearchHash(self,hash)

  def __init__(self) :
    self.api_key = os.getenv("Tour_Api")  
    self.headers = {
      "User-Agent" : "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36"
    }
    self.area_code_list = self.AREA_CODE_LIST()
    # 로딩 속도 향상을 위해서 값을 받아온 후 리스트로 나열함.
    self.content_type_list = {
      12: "관광지",
      14: "문화시설",
      15: "축제",
      25: "여행코스",
      28: "레포츠",
      32: "숙박",
      38: "쇼핑",
      39: "음식점"
    }
    self.rcontent_type_list = {
        name: id for id, name in self.content_type_list.items()
    }
    self.type_list = {
    "AC": "숙박",
    "EX": "체험",
    "FD": "음식",
    "HS": "역사",
    "NA": "자연",
    "SH": "쇼핑",
    "VE": "문화"
    }
    self.cat1_list = {'A01': '자연', 'A02': '인문(문화/예술/역사)', 'A03': '레포츠', 'A04': '쇼핑', 'A05': '음식', 'B02': '숙박', 'C01': '추천코스'}
    self.cat2_list = {
      "A01": {'A0101': '자연관광지', 'A0102': '관광자원'},
      "A02": {'A0201': '역사관광지', 'A0202': '휴양관광지', 'A0203': '체험관광지', 'A0204': '산업관광지', 'A0205': '건축/조형물', 'A0206': '문화시설', 'A0207': '축제', 'A0208': '공연/행사'},
      "A03": {'A0301': '레포츠소개', 'A0302': '육상 레포츠', 'A0303': '수상 레포츠', 'A0304': '항공 레포츠', 'A0305': '복합 레포츠'},
      "A04": {'A0401': '쇼핑'},
      "A05": {'A0502': '음식점'},
      "B02": {'B0201': '숙박시설'},
      "C01": {'C0112': '가족코스', 'C0113': '나홀로코스', 'C0114': '힐링코스', 'C0115': '도보코스', 'C0116': '캠핑코스', 'C0117': '맛코스'}
    }
    self.cat3_list = {
      "A0101": {'A01010100': '국립공원', 'A01010200': '도립공원', 'A01010300': '군립공원', 'A01010400': '산', 'A01010500': '자연생태관광지', 'A01010600': '자연휴양림', 'A01010700': '수목원', 'A01010800': '폭포', 'A01010900': '계곡', 'A01011000': '약수터', 'A01011100': '해안절경', 'A01011200': '해수욕장', 'A01011300': '섬', 'A01011400': '항구/포구', 'A01011600': '등대', 'A01011700': '호수', 'A01011800': '강', 'A01011900': '동굴'}, 
      "A0102": {'A01020100': '희귀동.식물', 'A01020200': '기암괴석'}, 
      "A0201": {'A02010100': '고궁', 'A02010200': '성', 'A02010300': '문', 'A02010400': '고택', 'A02010500': '생가', 'A02010600': '민속마을', 'A02010700': '유적지/사적지', 'A02010800': '사찰', 'A02010900': '종교성지', 'A02011000': '안보관광'}, 
      "A0202": {'A02020200': '관광단지', 'A02020300': '온천/욕장/스파', 'A02020400': '이색찜질방', 'A02020500': '헬스투어', 'A02020600': '테마공원', 'A02020700': '공원', 'A02020800': '유람선/잠수함관광'}, 
      "A0203": {'A02030100': '농.산.어촌 체험', 'A02030200': '전통체험', 'A02030300': '산사체험', 'A02030400': '이색체험', 'A02030600': '이색거리'}, 
      "A0204": {'A02040400': '발전소', 'A02040600': '식음료', 'A02040800': '기타', 'A02040900': '전자-반도체', 'A02041000': '자동차'}, 
      "A0205": {'A02050100': '다리/대교', 'A02050200': '기념탑/기념비/전망대', 'A02050300': '분수', 'A02050400': '동상', 'A02050500': '터널', 'A02050600': '유명건물'}, 
      "A0206": {'A02060100': '박물관', 'A02060200': '기념관', 'A02060300': '전시관', 'A02060400': '컨벤션센터', 'A02060500': '미술관/화랑', 'A02060600': '공연장', 'A02060700': '문화원', 'A02060800': '외국문화원', 'A02060900': '도서관', 'A02061000': '대형서점', 'A02061100': '문화 전수시설', 'A02061200': '영화관', 'A02061300': '어학당', 'A02061400': '학교'}, 
      "A0207": {'A02070100': '문화관광축제', 'A02070200': '일반축제'}, 
      "A0208": {'A02080100': '전통공연', 'A02080200': '연극', 'A02080300': '뮤지컬', 'A02080400': '오페라', 'A02080500': '전시회', 'A02080600': '박람회', 'A02080800': '무용', 'A02080900': '클래식음악회', 'A02081000': '대중콘서트', 'A02081100': '영화', 'A02081200': '스포츠경기', 'A02081300': '기타행사', 'A02081400': '넌버벌'}, 
      "A0301": {'A03010200': '수상레포츠', 'A03010300': '항공레포츠'}, 
      "A0302": {'A03020200': '수련시설', 'A03020300': '경기장', 'A03020400': '인라인(실내 인라인 포함)', 'A03020500': '자전거하이킹', 'A03020600': '카트', 'A03020700': '골프', 'A03020800': '경마', 'A03020900': '경륜', 'A03021000': '카지노', 'A03021100': '승마', 'A03021200': '스키/스노보드', 'A03021300': '스케이트', 'A03021400': '썰매장', 'A03021500': '수렵장', 'A03021600': '사격장', 'A03021700': '야영장,오토캠핑장', 'A03021800': '암벽등반', 'A03022000': '서바이벌게임', 'A03022100': 'ATV', 'A03022200': 'MTB'}, 
      "A0303": {'A03030100': '윈드서핑/제트스키', 'A03030200': '카약/카누', 'A03030300': '요트', 'A03030400': '스노쿨링/스킨스쿠버다이빙', 'A03030500': '민물낚시', 'A03030600': '바다낚시', 'A03030700': '수영', 'A03030800': '래프팅'},
      "A0304": {'A03040100': '스카이다이빙', 'A03040200': '초 경량비행', 'A03040300': '헹글라이딩/패러글라이딩', 'A03040400': '열기구'}, 
      "A0305": {'A03050100': '복합 레포츠'}, 
      "A0401": {'A04010100': '5일장', 'A04010200': '상설시장', 'A04010300': '백화점', 'A04010400': '면세점', 'A04010500': '대형 마트', 'A04010600': '전문매장/상가', 'A04010700': '공예/공방', 'A04010900': '특산물판매점', 'A04011000': '사후면세점', 'A04011200': '스키(보드) 렌탈샵'}, 
      "A0502": {'A05020100': '한식', 'A05020200': '서양식', 'A05020300': '일식', 'A05020400': '중식', 'A05020700': '이색음식점', 'A05020900': '카페/전통찻집', 'A05021000': '클럽'}, 
      "B0201": {'B02010100': '관광호텔', 'B02010500': '콘도미니엄', 'B02010600': '유스호스텔', 'B02010700': '펜션', 'B02010900': '모텔', 'B02011000': '민박', 'B02011100': '게스트하우스', 'B02011200': '홈스테이', 'B02011300': '서비스드레지던스', 'B02011600': '한옥'}, 
      "C0112": {'C01120001': '가족코스'}, 
      "C0113": {'C01130001': '나홀로코스'}, 
      "C0114": {'C01140001': '힐링코스'}, 
      "C0115": {'C01150001': '도보코스'}, 
      "C0116": {'C01160001': '캠핑코스'}, 
      "C0117": {'C01170001': '맛코스'}
    }

  #데이터 꺼내기
  def AccessData(self, param={}, url=""):
    #url이 일치하지 않을 경우
    #params이 일치하지 않을 경우
    url = f"https://apis.data.go.kr/B551011/KorService2/{url}"

    params = {
      "MobileOS": "WEB",
      "MobileApp": "AppTest",
      "serviceKey": str(self.api_key),
      "_type": "json",
      "numOfRows": 10
    }
    params.update(param)
    try:
      # print("params:",params,", url:", url)
      response = requests.get(url,headers=self.headers, params=params)
      # print(response.status_code)
      contents = response.text
      # print(contents)

      #json.loads()를 사용하여 문자열을 파이썬 딕셔너리로 변환
      data_dict = json.loads(contents)
    ############################
    except requests.exceptions.RequestException as e:
        # 네트워크 오류, 타임아웃, HTTP 오류(4xx, 5xx) 발생 시
        print(f"API 요청 실패 (네트워크/HTTP): {e}")
        return None  # None 반환
    except json.JSONDecodeError as e:
        # 응답이 JSON 형식이 아닐 때
        print(f"API 응답 JSON 디코딩 실패: {e}")
        return None
    ############################
    item_data = (
      data_dict.get("response", {})
      .get("body", {})
      .get("items")
    )

    # item_data가 None이거나 빈 리스트/딕셔너리가 아닌지 확인
    if item_data is None or (isinstance(item_data, (dict, list)) and not item_data):
      return None
    
    if isinstance(item_data, dict):
      return item_data
    
    return item_data
  #콘텐츠 타입
  def CONTENT_TYPE_REVERSE_MAPPING(self) :
    return {value : key for key, value in self.content_type_list.items()}
    

  #콘텐츠 타입으로 매핑
  def CONTENT_TYPE_MAPPING(self, value) :
    # id -> name
    if isinstance(value, int):
      mapping_data = self.content_type_list.get(value, value)
    # name -> id   
    elif isinstance(value, str):
      mapping_data = self.rcontent_type_list.get(value, value)
    else:
      mapping_data = value
    return mapping_data
  
  #타입 매핑
  def TYPE_MAPPING(self, type):
    return self.type_list.get(type, type)
    
  #카테고리 매핑
  def CATEGORY_CODE_MAPPING(self, cat):
    url_key = f"categoryCode2"
    param = {
    }
    # ex)A01010900
    cat = cat.strip()
    cat1 = cat[:3]   #A01
    cat2 = cat[3:5]  #01
    cat3 = cat[5:]   #0900

    # code의 전까지 cat을 param에 넣어야 code이름을 찾을 수 있다.
    if cat3:
      return self.cat3_list[cat1 + cat2][cat]
    if cat2:
      return self.cat2_list[cat1][cat]
      
    return self.cat1_list[cat1]
    # print(param)

    # item_data = self.AccessData(url = url_key, param = param)
    # items = item_data.get("item", [])

    # items_mapping = {item["code"]: item["name"] for item in items}
    # print(items_mapping)
    # return items_mapping
    # for item in items:
    #   if item["code"] == cat:
    #     # print(item["name"])
    #     return item["name"]

  #카테고리 불러오기
  def CATEGORY_CODE_CALL(self, cat):
    url_key = f"categoryCode2"
    param = {
    }
    #A01010900
    cat = cat.strip()
    cat1 = cat[:3]   #A01
    cat2 = cat[3:5]  #01
    cat3 = cat[5:]   #0900

    # code의 전까지 cat을 param에 넣어야 code이름을 찾을 수 있다.
    if cat1:
      param["cat1"] = cat1
    if cat2:
      param["cat2"] = cat1 + cat2
    if cat3:
      param["cat3"] = cat
    # print(param)

    item_data = self.AccessData(url = url_key, param = param)
    items = item_data.get("item", [])

    items_mapping = {item["code"]: item["name"] for item in items}
    return items_mapping

  #지역코드로 조회
  def AREA_CODE_LIST(self) :
    url_key = f"areaCode2"
    param = {
      #전체결과조회
      "numOfRows": 20 
    }
    item_data = self.AccessData(url = url_key, param = param)

    items = item_data.get("item", [])

    # [{'rnum': 1, 'code': '1', 'name': '서울'}, {'rnum': 2, 'code': '2', 'name': '인천'}, {'rnum': 3, 'code': '3', 'name': '대전'}, {'rnum': 4, 'code': '4', 'name': '대구'}, {'rnum': 5, 'code': '5', 'name': '광주'}, {'rnum': 6, 'code': '6', 'name': '부산'}, {'rnum': 7, 'code': '7', 'name': '울산'}, {'rnum': 8, 'code': '8', 'name': '세종특별자치시'}, {'rnum': 9, 'code': '31', 'name': '경기도'}, {'rnum': 10, 'code': '32', 'name': '강원특별자치도'}, {'rnum': 11, 'code': '33', 'name': '충청북도'}, {'rnum': 12, 'code': '34', 'name': '충청남도'}, {'rnum': 13, 'code': '35', 'name': '경상북도'}, {'rnum': 14, 'code': '36', 'name': '경상남도'}, {'rnum': 15, 'code': '37', 'name': '전북특별자치도'}, {'rnum': 16, 'code': '38', 'name': '전라남도'}, {'rnum': 17, 'code': '39', 'name': '제주특별자치도'}]
    return items

  #지역기반 조회
  #전체결과조회하기 위해서


  #지역코드 매핑
  def AREA_CODE_MAPPING(self,areacode) :
    items = self.area_code_list
    item = next((i for i in items if i.get("code") == str(areacode)), None)
    

    #item = [item for item in item_data if item_data.get("code") == areaCode]
    if item is not None:
      item_name = item.get("name")
      return item_name
    else:
      return "지역 미확인"

  def AREA_NAME_MAPPING(self,areaname) :
    items = self.area_code_list

    item = next((i for i in items if i.get("name") == str(areaname)), None)

    if item is not None:
            item_code = item.get("code")
            return item_code
    else:
        return "코드 미확인"

  #콘텐츠 아이디로 조회
  def SearchCID(self,cid) :
    url_key = f"detailCommon2"
    param = {
      "pageNo": "1",
      "contentId": cid,
    }
    
    item_data = self.AccessData(url = url_key, param = param)


    item = item_data.get("item", [{}])[0]
    
    # item = data_dict["response"]["body"]["items"]["item"][0]
    # data = { "id" : item["contentid"], "title" : item["title"], "image" : item["firstimage"], "intro" : item["overview"]}
    

    # 키가 없으면 None
    data = {
      "id" : item.get("contentId"),           
      "contenttype": (
          self.CONTENT_TYPE_MAPPING(int(item.get("contenttypeid", 0)))  
        ),         
      "title" : item.get("title"),          
      "image" : item.get("firstimage"),      
      "intro" : item.get("overview"),
      "addr1" : item.get("addr1"),
      "mapx" : item.get("mapx"),
      "mapy" : item.get("mapy"),

      "type" : self.TYPE_MAPPING(item.get("lclsSystm1")),
      "typecode1": item.get("lclsSystm1"),
      "area" : self.AREA_CODE_MAPPING(item.get("areacode")),
      "areacode" : item.get("areacode"),
      "cat3" : item.get("cat3"),
      "cat3_name" : self.CATEGORY_CODE_MAPPING(item.get("cat3"))
    }
    return data

  # 키워드로 조회
  def SearchKeyword(self, area=None, cat=None, keyword="", type="AC", page = 1) :
    url_key = f"searchKeyword2"
    param = {
      "pageNo": "1",
      "arrange": "O",
      "numOfRows": "10",
      #"lclsSystm1" : {"AC", "EV", "EX", "FD", "HS", "LS", "NA", "SH", "VE"},
      "keyword": keyword
    }
    if page is not None and page != 1:
      param["pageNo"] = page
    
    if type is not None and type != "":
      param["lclsSystm1"] = type
    else:
      param["lclsSystm1"] = "AC"

    if area is not None and area != "":
      param["areaCode"] = area

    if cat is not None and cat != "":
      #A01010900
      cat = cat.strip()
      cat1 = cat[:3]   #A01

      if cat1:
        param["cat1"] = cat1
        cat2 = cat[3:5]  #01
        if cat2:
          param["cat2"] = cat1 + cat2
          cat3 = cat[5:]   #0900
          if cat3:
            param["cat3"] = cat

    # print("param", param)
    item_data = self.AccessData(url = url_key, param = param)

    if not item_data:
      items = []
    else:
      items = item_data.get("item", [])
 
    datas = [
      {
        "id" : i.get("contentid"),
        "title" : i.get("title"),
        "addr1" : i.get("addr1"),
        "image" : i.get("firstimage"),
        "typecode1": i.get("lclsSystm1"),
        "type": self.TYPE_MAPPING(i.get("lclsSystm1")),
        "area" : self.AREA_CODE_MAPPING(i.get("areacode")),
        "areacode" : i.get("areacode"),
        "mapX" : i.get("mapx"),
        "mapY" : i.get("mapy"),
        "cat3" : i.get("cat3"),
        "cat3_name" : self.CATEGORY_CODE_MAPPING(i.get("cat3"))
      }
      for i in items
    ]
    data_dict = {
      "type" : type,
      "value": datas
    }

    #print(data)
    return data_dict

  #지역으로 찾기
  def SearchArea(self,  area=None, cat=None, type="AC", page = 1) :
    url_key = f"areaBasedList2"
    param = {
        "arrange" : "O",
        "lclsSystm1" : type
    }
    if page is not None and page != 1:
      param["pageNo"] = page
    
    if type is not None and type != "":
      param["lclsSystm1"] = type
    else:
      param["lclsSystm1"] = "AC"

    if area is not None and area != "":
      param["areaCode"] = area

    if cat is not None and cat != "":
      #A01010900
      cat = cat.strip()
      cat1 = cat[:3]   #A01

      if cat1:
        param["cat1"] = cat1
        cat2 = cat[3:5]  #01
        if cat2:
          param["cat2"] = cat1 + cat2
          cat3 = cat[5:]   #0900
          if cat3:
            param["cat3"] = cat

    # print("param", param)
    item_data = self.AccessData(url = url_key, param = param) 
    items = item_data.get("item", [])
    datas = [
        {
          "id" : i.get("contentid"),
          "title" : i.get("title"),
          "addr1" : i.get("addr1"),
          "image" : i.get("firstimage"),
          "typecode1": i.get("lclsSystm1"),
          "type": self.TYPE_MAPPING(i.get("lclsSystm1")),
          "area" : self.AREA_CODE_MAPPING(i.get("areacode")),
          "areacode" : i.get("areacode"),
          "mapX" : i.get("mapx"),
          "mapY" : i.get("mapy"),
          "cat3" : i.get("cat3"),
          "cat3_name" : self.CATEGORY_CODE_MAPPING(i.get("cat3"))
        }
        for i in items
      ]

    data_dict = {
      "type" : type,
      "value": datas
    }
    return data_dict

# api_service = APIService()
# print(api_service.SearchKeyword(keyword="와룡산"))
# # print(api_service.CATEGORY_CODE_MAPPING('A01010100'))
# aa = [f'{k}: {api_service.CATEGORY_CODE_CALL(k)}' for key, val in api_service.cat2_list.items() for k in val.keys()]
# print(aa)