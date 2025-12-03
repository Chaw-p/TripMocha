
import requests
import json
from dotenv import load_dotenv
import os

# pip install python-dotenv

load_dotenv()

class APIService :
  
  def __init__(self) :
    self.api_key = os.getenv("Tour_Api")  
    self.headers = {
      "User-Agent" : "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36"
    }
  
  #콘텐츠 타입
  def CONTENT_TYPE_MAPPING(self, contenttypeid) :

    CONTENT_TYPE_MAPPING = {
    12: "관광지",
    14: "문화시설",
    15: "축제",
    25: "여행코스",
    28: "레포츠",
    32: "숙박",
    38: "쇼핑",
    39: "음식점"
    }

    mapping_data = CONTENT_TYPE_MAPPING.get(contenttypeid, contenttypeid)

    return mapping_data
  def Area_Code(self) :
    

  #콘텐츠 아이디로 조회
  def GetData(self,id) :
    url = f"https://apis.data.go.kr/B551011/KorService2/detailCommon2"
    params = {
        "numOfRows": "10",
        "pageNo": "1",
        "MobileOS": "WEB",
        "MobileApp": "AppTest",
        "serviceKey": str(self.api_key),
        "_type": "json",
        "contentId": id,
    }
    response = requests.get(url,headers=self.headers, params=params)
    #print(response.status_code)
    contents = response.text
    #print(contents)

    #json.loads()를 사용하여 문자열을 파이썬 딕셔너리로 변환
    data_dict = json.loads(contents)

    #print("--- 딕셔너리 변환 결과 ---")
    #print(type(data_dict)) # <class 'dict'>
    #print("-" * 20)

    #딕셔너리 접근 방식을 사용하여 데이터 추출
    # data_dict에 "response" 키가 없으면 None이 할당됩니다.
    item_data = (
      data_dict.get("response", {})
      .get("body", {})
      .get("items", {})
    )

    if not isinstance(item_data, dict):
      item_data = {}

    item = item_data.get("item", [{}])[0]
    
    # item = data_dict["response"]["body"]["items"]["item"][0]
    # data = { "id" : item["contentid"], "title" : item["title"], "image" : item["firstimage"], "intro" : item["overview"]}
    

    # 키가 없으면 None
    data = {
      "id" : item.get("contentid"),           
      "title" : item.get("title"),          
      "image" : item.get("firstimage"),      
      "intro" : item.get("overview"),
      "mapx" : item.get("mapx"),
      "mapy" : item.get("mapy")
    }
    return data

  # 키워드로 조회
  def SearchData(self,keyword) :
    url = f"https://apis.data.go.kr/B551011/KorService2/searchKeyword2"
    params = {
      "numOfRows": "10",
      "pageNo": "1",
      "MobileOS": "WEB",
      "MobileApp": "AppTest",
      "serviceKey": str(self.api_key),
      "_type": "json",
      "arrange": "O",
      "keyword": keyword
    }
    response = requests.get(url,headers=self.headers, params=params)
    #print(response.status_code)
    contents = response.text
    #print(contents)
    
    #json.loads()를 사용하여 문자열을 파이썬 딕셔너리로 변환
    data_dict = json.loads(contents)

    #print("--- 딕셔너리 변환 결과 ---")
    #print(type(data_dict)) # <class 'dict'>
    #print("-" * 20)

    #딕셔너리 접근 방식을 사용하여 데이터 추출
    
    # data_dict에 키가 없으면 None이 할당됩니다.

    item_data = (
      data_dict.get("response", {})
      .get("body", {})
      .get("items", {})
    )

    if not isinstance(item_data, dict):
      item_data = {}

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
        )
      }
      for i in items
    ]
    print(datas)

    #print(data)
    return datas
