import pandas as pd
import pickle
import pymysql

# ----------------------------------------------------------------------
# 1. 🚨 DB 연결 정보 설정 (사용자 환경에 맞게 반드시 수정하세요!)
# ----------------------------------------------------------------------
DB_CONFIG = {
    'host': '192.168.60.133',  # 예: 'localhost'
    'user': 'tripmocha',
    'password': 'ezen',
    'db': 'tripmocha', # 실제 데이터베이스 이름
    'charset': 'utf8mb4'
}
TABLE_NAME = 'city_county'  # ADM Code가 있는 테이블
ADM_CODE_COLUMN = 'adm_code'  # 🚨 실제 DB의 ADM Code 컬럼 이름으로 수정!
OUTPUT_FILE = 'adm_code_to_text.pkl' # Flask 로드 파일과 이름 통일 (area_mapping.pkl에서 변경)

# ----------------------------------------------------------------------
# 2. DB 연결 및 데이터 로드
# ----------------------------------------------------------------------
try:
    # 💡 pymysql.connect에 필요한 모든 인수를 전달
    conn = pymysql.connect(**DB_CONFIG) 

    # 🚨 SQL 쿼리 수정: ADM Code를 CHAR(문자열)로 캐스팅
    query = f"""
    SELECT 
        CAST({ADM_CODE_COLUMN} AS CHAR) AS adm_code_numeric,
        sido, 
        sigungu
    FROM {TABLE_NAME}
    """
    
    # 쿼리 실행 및 DataFrame으로 로드
    adm_df = pd.read_sql(query, conn)
    conn.close()
    
    print("✅ DB 연결 및 지역 코드 데이터 로드 완료.")

except Exception as e:
    print(f"❌ DB 연결 또는 데이터 로드 중 오류 발생: {e}")
    # 오류 발생 시 스크립트를 즉시 종료
    exit()

# ----------------------------------------------------------------------
# 3. 매핑 딕셔너리 생성 (로직 유지)
# ----------------------------------------------------------------------
def create_adm_key(row):
    sido = str(row['sido']).strip()
    sigungu = str(row['sigungu']).strip()

    # 시/군/구가 유효하지 않으면 시/도만 반환
    if not sigungu or sigungu.lower() in ['nan', 'none', '']:
        return sido
    
    return f"{sido} {sigungu}"

# ADM Code를 키, 주소 텍스트를 값으로 매핑
adm_df['adm_key_text'] = adm_df.apply(create_adm_key, axis=1)

ADM_CODE_TO_TEXT = pd.Series(
    adm_df['adm_key_text'].values, 
    index=adm_df['adm_code_numeric']
).to_dict()

# ----------------------------------------------------------------------
# 4. .pkl 파일로 저장 (OUTPUT_FILE 이름으로 저장)
# ----------------------------------------------------------------------
try:
    with open(OUTPUT_FILE, 'wb') as f:
        pickle.dump(ADM_CODE_TO_TEXT, f)
    
    print(f"✅ 매핑 딕셔너리가 '{OUTPUT_FILE}'로 성공적으로 저장되었습니다.")
    print("--- 매핑 예시 (상위 5개) ---")
    
    example_count = 0
    for code, text in ADM_CODE_TO_TEXT.items():
        if example_count < 5:
            print(f"코드 {code} : {text}")
            example_count += 1
        else:
            break
            
except Exception as e:
    print(f"❌ 매핑 파일 저장 중 오류 발생: {e}")