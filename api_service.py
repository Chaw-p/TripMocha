
import requests
import json
from dotenv import load_dotenv
import os

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
    # print("params:",params,", url:", url)
    response = requests.get(url,headers=self.headers, params=params)
    # print(response.status_code)
    contents = response.text
    # print(contents)

    #json.loads()를 사용하여 문자열을 파이썬 딕셔너리로 변환
    data_dict = json.loads(contents)

    item_data = (
      data_dict.get("response", {})
      .get("body", {})
      .get("items", {})
    )

    if not isinstance(item_data, dict):
      item_data = {}

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
      "mapy" : item.get("mapy")
    }
    return data

  # 키워드로 조회
  def SearchKeyword(self, keyword="") :
    url_key = f"searchKeyword2"
    param = {
      "pageNo": "1",
      "arrange": "O",
      "keyword": keyword
    }
    
    item_data = self.AccessData(url = url_key, param = param)

    # 추출된 item_data를 사용하여 id와 title을 안전하게 추출
    items = item_data.get("item", [])

    datas = [
      {
       "id" : i.get("contentid"),
       "title" : i.get("title"),
       "addr1" : i.get("addr1"),
       "image" : i.get("firstimage"),
       "contenttypeid": (
          self.CONTENT_TYPE_MAPPING(int(i.get("contenttypeid", 0)))  
          #CONTENT_TYPE_MAPPING.get(int(i.get("contenttypeid", 0)), i.get("contenttypeid"))
        ),
        "areacode" : self.AREA_CODE_MAPPING(i.get("areacode"))
      }
      for i in items
    ]

    #print(data)
    return datas

  def SearchArea(self, area=None, type=None) :
    url_key = f"areaBasedList2"
    param = {
        "arrange" : "O"
    }
    if area:
      param["areaCode"] = area
    if type:
      param["contentTypeId"] = type
    
    item_data = self.AccessData(url = url_key, param = param)  
    
    items = item_data.get("item", [])
    datas = [
      {
       "id" : i.get("contentid"),
       "title" : i.get("title"),
       "addr1" : i.get("addr1"),
       "image" : i.get("firstimage"),
       "contenttypeid": (
          self.CONTENT_TYPE_MAPPING(int(i.get("contenttypeid", 0)))  
          #CONTENT_TYPE_MAPPING.get(int(i.get("contenttypeid", 0)), i.get("contenttypeid"))
        ),
        "areacode" : self.AREA_CODE_MAPPING(i.get("areacode"))
      }
      for i in items
    ]
    return datas

  def SearchHash(self, hash) :
    area = self.AREA_NAME_MAPPING(hash)
    if  area != "코드 미확인":
      #지역으로 찾기를 실행한다.
      #area = self.AREA_NAME_MAPPING(hash)
      data = self.SearchArea(area = area)
      print("지역찾기")
    
    elif self.CONTENT_TYPE_MAPPING != hash:
      type = self.CONTENT_TYPE_MAPPING(hash)
      data = self.SearchArea(type = type)
      print("타입찾기")

    return data


api_service = APIService()

