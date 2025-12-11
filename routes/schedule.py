from flask import jsonify, request, Blueprint, render_template
from .models import db, CityCounty 
from dotenv import load_dotenv
import os
import pickle
from catboost import CatBoostRegressor
import pandas as pd
import numpy as np

load_dotenv()
key = os.getenv("choakey")

schedule_bp = Blueprint("schedule", __name__, url_prefix="/schedule")


# 실제 피클 모델 피처 이름 비교
FINAL_MODEL_FEATURES = [
    'VISIT_AREA_TYPE_CD', 
    'TRAVEL_STYL_3', 
    'TRAVEL_PERSONA', 
    'TRAVEL_STATUS_ACCOMPANY', 
    'TRAVEL_MISSION_INT', 
    'VISIT_AREA_NM', 
    'LOTNO_ADDR', 
    'X_COORD', 
    'Y_COORD', 
    'SEASON' 
]

# 범주형 피처 이름 비교 
categorical_features_names = [
    'VISIT_AREA_TYPE_CD', 
    'TRAVEL_STYL_3', 
    'TRAVEL_PERSONA', 
    'TRAVEL_STATUS_ACCOMPANY',
    'TRAVEL_MISSION_INT', 
    'VISIT_AREA_NM', 
    'LOTNO_ADDR', 
    'SEASON' 
]


try:
    with open('static/pkl/catboost_data.pkl', 'rb') as f:
        catboost_model = pickle.load(f)

    #db지역이름 매핑
    with open('static/pkl/travel_candidates_for_flask.pkl', 'rb') as f:
        travel_candidates_df = pickle.load(f) 
        travel_candidates_df['ADM_CODE_NUMERIC'] = travel_candidates_df['ADM_CODE_NUMERIC'].astype(str)

    with open('static/pkl/TAG_MAPPING.pkl', 'rb') as f:
        TAG_MAPPING = pickle.load(f) 
        
    print("피클 파일 로드 완료")
 
except Exception as e:
    print(f" 피클 파일 오류: {e}")
    catboost_model = None
    travel_candidates_df = pd.DataFrame()
    TAG_MAPPING = {}
    FINAL_MODEL_FEATURES = []
    categorical_features_names = []


#메인 / db 연결
@schedule_bp.route("/", methods=["GET"])
def main():
    destinations = db.session.query(
        CityCounty.sido,
        CityCounty.sigungu,
        db.func.max(CityCounty.latitude).label('latitude'),
        db.func.max(CityCounty.longitude).label('longitude'),
        db.func.max(CityCounty.adm_code).label('adm_code')
    ).group_by(
        CityCounty.sido,
        CityCounty.sigungu
    ).all()
    
    processed_destinations = [
        {
            'city_name': f"{d.sido} {d.sigungu}", 
            'sido': d.sido, 
            'sigungu': d.sigungu, 
            'adm_code': d.adm_code,
            'latitude': d.latitude,
            'longitude': d.longitude,
            'data_destination': f"{d.sido} {d.sigungu}" 
        } for d in destinations
    ]
    return render_template("schedule/schedule_main.html", destinations=processed_destinations)

# 특징생성함수
import pandas as pd

def create_catboost_input(target_df, duration_days, theme_tags, TAG_MAPPING, FINAL_MODEL_FEATURES, categorical_features_names):

    input_df = target_df.copy()

    try:
        input_df['DURATION'] = int(duration_days)
    except (ValueError, TypeError):
        input_df['DURATION'] = 1 

    theme_tag_columns = [col for col in FINAL_MODEL_FEATURES if col.endswith('_TAG')]
    
    for tag_col in theme_tag_columns:
        if tag_col not in input_df.columns:
         
            input_df[tag_col] = 0

    for user_tag in theme_tags:
        tag_feature_name = TAG_MAPPING.get(user_tag.upper()) 
        
        if tag_feature_name and tag_feature_name in input_df.columns:
           
            input_df[tag_feature_name] = 1
        
    missing_cols = [col for col in FINAL_MODEL_FEATURES if col not in input_df.columns]
    if missing_cols:
        for col in missing_cols:
             # 임시로 0으로 채우지만, 범주형(CATEGORY)인지 수치형(NUMERIC)인지 확인 필요
             input_df[col] = 0 

    numeric_features = [col for col in FINAL_MODEL_FEATURES if col not in categorical_features_names]
    input_df[numeric_features] = input_df[numeric_features].fillna(0.0)
    

    input_df[categorical_features_names] = input_df[categorical_features_names].fillna('')
    return input_df[FINAL_MODEL_FEATURES]


#여행만들기 (여행지,날짜,인원,여행테마)
@schedule_bp.route("/recommend", methods=["POST"])
def recommend_schedule():
    data = request.get_json()
    adm_code = str(data.get('adm_code'))

    if not adm_code:
     return jsonify({"error": "여행지(adm_code)가 누락되었습니다."}), 400
    
    #원파일주소수정없이 코드로 수정 (시도/시군구)
    if len(adm_code) >= 5:
    # 11110 (종로구) -> 11 (서울시)
     filtered_adm_code = adm_code[:2] 
    else:
        # 지방  (예: 세종시, 36)
        filtered_adm_code = adm_code

    # 2. 필터링 로직 수정: ADM_CODE_NUMERIC의 시작 부분이 광역 코드와 일치하는지 확인
    # str[:2]를 사용하여 데이터프레임의 모든 행을 2자리 코드로 비교합니다.
    try:
        target_df = travel_candidates_df[
            travel_candidates_df['ADM_CODE_NUMERIC'].str.startswith(filtered_adm_code)
        ].copy()
        
    except Exception as e:
        return jsonify({"error": f"데이터 필터링 중 오류: {e}"}), 500

    duration_days = data.get('duration_days', 1) 
    theme_tags = data.get('theme_tags', [])

    sido_nm = data.get('destination', {}).get('sido_nm', '?')
    sigungu_nm = data.get('destination', {}).get('sigungu_nm', '?')

    if not adm_code:
        return jsonify({"error": "여행지(adm_code)가 누락되었습니다."}), 400
    
    filtered_adm_code = adm_code[:5] if len(adm_code) > 5 else adm_code
   
    if travel_candidates_df.empty or catboost_model is None:
        return jsonify({"error": "서버 데이터 로드 실패. 관리자에게 문의하세요."}), 500

    # 1. 추천 후보 필터링 (ADM_CODE_NUMERIC 컬럼 사용)
    try:
        target_df = travel_candidates_df[travel_candidates_df['ADM_CODE_NUMERIC'] == filtered_adm_code].copy()
        
    except KeyError:
        return jsonify({"error": "데이터 필터링 중 내부 오류 (ADM_CODE_NUMERIC 컬럼 없음)."}), 500

    if target_df.empty:
        return jsonify({"error": "해당 지역의 추천 후보지가 없습니다."}), 200

    duration_days = data.get('duration_days', 1) 
    theme_tags = data.get('theme_tags', [])

    # 2. 모델 입력 특징 벡터 생성
    try:
        X_predict = create_catboost_input(
            target_df.drop(columns=['ADM_CODE_NUMERIC'], errors='ignore'),
            duration_days, 
            theme_tags, 
            TAG_MAPPING, 
            FINAL_MODEL_FEATURES, 
            categorical_features_names
        )
    except Exception as e:
        print(f" create_catboost_input 함수 오류: {e}") 
        return jsonify({"error": "입력 데이터 생성 중 오류 발생."}), 500
  
    try:
        scores = catboost_model.predict(X_predict)
    except Exception as e:
        print(f"CatBoost 예측 오류: {e}")
        return jsonify({"error": "모델 예측 중 오류 발생."}), 500
    
    # 4. 추천 결과 생성 및 JSON 반환, 일정 개수(head)
    
    target_df['SCORE'] = scores
    sorted_df = target_df.sort_values(by='SCORE', ascending=False)

    #추가 필터링
    exclude_mask = target_df['VISIT_AREA_NM'].str.contains('호텔', case=False, na=False) | \
    target_df['VISIT_AREA_NM'].str.contains('아파트', case=False, na=False) | \
    target_df['VISIT_AREA_NM'].str.contains('오피스텔', case=False, na=False) | \
    target_df['VISIT_AREA_NM'].str.contains('점', case=False, na=False)
    filtered_target_df = target_df[~exclude_mask].copy()
    sorted_df = filtered_target_df.sort_values(by='SCORE', ascending=False)

    diverse_main_candidates = sorted_df.drop_duplicates(
    subset=['VISIT_AREA_TYPE_CD'], 
    keep='first'
    ).copy()
    
    recommended_df = diverse_main_candidates.head(3)
    
    recommended_df['DURATION'] = int(duration_days)
    recommended_df['SIDO_NM'] = sido_nm
    recommended_df['SIGUNGU_NM'] = sigungu_nm

    recommended_trips_list = recommended_df.to_dict('records')

    # 메인 장소 추천 후 반복문
    
    for trip in recommended_trips_list:
        main_area_nm = trip['VISIT_AREA_NM']
        target_adm_code = trip['ADM_CODE_NUMERIC']
        target_type_cd = trip.get('VISIT_AREA_TYPE_CD') or trip.get('TRAVEL_MISSION_INT')
        
        related_places = []

        # 1단계 추천 3개의 목록 (동일지역, 동일테마)
        if target_type_cd is not None:
            strict_filter = (sorted_df['ADM_CODE_NUMERIC'] == target_adm_code) & \
                            (sorted_df['VISIT_AREA_TYPE_CD'] == target_type_cd) & \
                            (sorted_df['VISIT_AREA_NM'] != main_area_nm) 
            
            related_places.extend(sorted_df[strict_filter]['VISIT_AREA_NM'].head(3).tolist())

        # 2단계 추천 3개의 목록안에 5개의 일정 추천
        if len(related_places) < 5:
            current_places_set = set(related_places)
            needed_count = 5 - len(related_places)
            
            wide_filter = (sorted_df['ADM_CODE_NUMERIC'] == target_adm_code) & \
                        (sorted_df['VISIT_AREA_NM'] != main_area_nm)
            
            new_places_df = sorted_df[wide_filter].copy()
        
            # 2. 1단계에서 이미 선택된 장소의 이름 목록을 제외
        new_places_df = new_places_df[~new_places_df['VISIT_AREA_NM'].isin(current_places_set)]

        # 3. 1단계에서 이미 사용된 테마 코드 목록 확인
        existing_themes = sorted_df[sorted_df['VISIT_AREA_NM'].isin(current_places_set)]['VISIT_AREA_TYPE_CD'].unique().tolist()

        # 4. 남아있는 후보에서 이미 사용된 테마 코드를 제외
        new_places_df = new_places_df[~new_places_df['VISIT_AREA_TYPE_CD'].isin(existing_themes)]
        
        # 5. 🚨 테마 중복 제거: 점수가 가장 높은 장소(keep='first')를 남기고, 동일 테마는 제거합니다.
        diverse_places_df = new_places_df.drop_duplicates(subset=['VISIT_AREA_TYPE_CD'], keep='first')
        
        # 6. 필요한 개수만큼 장소 이름 가져오기
        new_places = diverse_places_df['VISIT_AREA_NM'].head(needed_count).tolist()
        
        related_places.extend(new_places)

        while len(related_places) < 5:
            related_places.append("추가 추천 장소 (데이터 부족)")
        
        trip['RELATED_PLACES'] = related_places[:5]
    
    return jsonify({
        "success": True,
        "recommended_trips": recommended_trips_list
    })


@schedule_bp.route("/view", methods=["GET"])
def view():
    return render_template("schedule/schedule_view.html", choakey=key)

@schedule_bp.route("/list", methods=["GET"])
def list():
    return render_template("schedule/schedule_list.html")