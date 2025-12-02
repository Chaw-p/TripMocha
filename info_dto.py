import requests
import os
from dotenv import load_dotenv

class Info_DTO :
  load_dotenv()
  apiKey = os.getenv("37241fb3be15e8f7ff12f2eeabe7001570fd01b65e94f15a6fa974aa722e86fc")

  url = "http://apis.data.go.kr/B551011/KorService2/detailCommon2?serviceKey={apiKey}"

  params = {
    "MobileApp" : "TestApp",
    "MobileOS" : "ETC",
    "numOfRows" : 10,
    "pageNo" : 1,
    "_type" : json
  }
  response = requests.get(url, params=params)
  print(response.status_code)
  print(response.json())

  def __init__(self):
    pass
   
   
   