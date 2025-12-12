# import pandas as pd
# import os

# from api_service import APIService

# # 현재 Python 스크립트가 실행되고 있는 폴더 경로를 출력합니다.
# print(os.getcwd())

# #csv 파일을 읽어들인다.
# df = pd.read_csv('merged_all_winter.csv', encoding='cp949')
# # print(df.head())
# # print("=" * 65)
# name = df["VISIT_AREA_NM"]
# df["contentid"] = pd.NA
# print("=" * 65)
# # print(len(df))

# for index, keyword in df["VISIT_AREA_NM"].iloc[25:30].items():
#     if not keyword:
#         continue
    
#     # 1. API 호출
#     api_response = APIService().SearchKeyword(keyword=keyword)
    
#     # 2. API 응답 유효성 검사 (NoneType 방지)
#     if api_response is not None:

#         content_id_list = api_response.get("value", []) 
        
#         # 4. 데이터가 유효한지 최종 확인
#         if content_id_list and isinstance(content_id_list, list) and len(content_id_list) > 0:
            
#             # 5. 첫 번째 검색 결과의 'id'를 추출합니다.
#             first_content_id = content_id_list[0].get("id") 
            
#             # 6. DataFrame의 해당 행에 할당합니다.
#             df.loc[index, "contentid"] = first_content_id
#             # print(f"  -> {keyword}: {df.loc[index, "contentid"]}")
            
#         # else:
#             # print(f"  -> {keyword}: API 검색 결과 (value)가 비어있습니다.")

#     else:
#         # api_response가 None인 경우 (API 통신 실패 또는 결과 없음)
#         print(f"  -> {keyword}: API 호출 또는 데이터 처리 실패로 'None' 반환됨.")
#         # 이 경우 df.loc[index, "contentid"]는 초기값(pd.NA)을 유지합니다.
        
# df.to_csv("merged_all_winter_add_id.csv", encoding='cp949')

# print("=" * 65)
# print(df[["VISIT_AREA_NM", "contentid"]].head(5))