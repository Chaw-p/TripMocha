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

    with open('static/pkl/trip_tag_mapping.pkl', 'rb') as f:
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
def create_catboost_input(target_df, duration_days, theme_tags, TAG_MAPPING, FINAL_MODEL_FEATURES, categorical_features_names):
    # 1. 사용자 조건 특징(DURATION, TAGS) 추출
    user_features = {'DURATION': int(duration_days)}
    mapped_theme_codes = {}
    
    for tag in theme_tags:
        theme_map = TAG_MAPPING.get(tag, {})
        for key, value in theme_map.items():
            if value is not None and key not in mapped_theme_codes:
                mapped_theme_codes[key] = value

    user_features.update(mapped_theme_codes)
    
    # 2. 모든 후보 행에 공통 특징을 복사하여 결합
    candidate_cols = ['VISIT_AREA_NM', 'LOTNO_ADDR', 'X_COORD', 'Y_COORD'] 
    X_predict = target_df[candidate_cols].copy()
    
    for col, val in user_features.items():
        X_predict[col] = val

    # 3. 모델 학습 시 사용된 최종 컬럼 순서 및 이름으로 정렬/필터링
    final_dfs = []
    
    for _, row in X_predict.iterrows():
        feature_values = []
        for feature in FINAL_MODEL_FEATURES:
            value = row.get(feature)
        
            if feature in categorical_features_names:
                # 범주형: 결측치(NaN, None)나 다른 타입은 빈 문자열로 처리
                if pd.isna(value) or value is None:
                    feature_values.append('') 
                else:
                    feature_values.append(str(value))
            
            # X_COORD, Y_COORD 및 DURATION 등 수치형
            else:
                # 수치형: 결측치(NaN, None)는 0.0으로 처리
                try:
                    feature_values.append(float(value) if pd.notna(value) else 0.0)
                except (ValueError, TypeError):
                    # 만약 숫자로 변환 불가능하면 0.0으로 대체
                    feature_values.append(0.0)
                
        final_dfs.append(feature_values)

    return pd.DataFrame(final_dfs, columns=FINAL_MODEL_FEATURES)

# # 장소추천
# def get_related_places_for_area(visit_area_nm, full_df): 
#     """
#     특정 VISIT_AREA_NM과 동일한 지역/테마의 실제 장소 목록을 반환합니다.
#     """
#     main_area_info = full_df[full_df['VISIT_AREA_NM'] == visit_area_nm].iloc[0]
#     target_adm_code = main_area_info['ADM_CODE_NUMERIC']
#     target_type_cd = main_area_info['VISIT_AREA_TYPE_CD']
    
#     related_places_df = full_df[
#         (full_df['ADM_CODE_NUMERIC'] == target_adm_code) & 
#         (full_df['VISIT_AREA_TYPE_CD'] == target_type_cd) &
#         (full_df['VISIT_AREA_NM'] != visit_area_nm) 
#     ]
    
#     related_places = related_places_df['VISIT_AREA_NM'].head(5).tolist()
    
#     # 만약 추천할거 데이터 없음 제미나이 추천사용
#     while len(related_places) < 5:
#         related_places.append("추가 추천 장소 (데이터 부족)")
        
#     return related_places[:5] # 방문지 최대 5개


#여행만들기 (여행지,날짜,인원,여행테마)
@schedule_bp.route("/recommend", methods=["POST"])
def recommend_schedule():
    data = request.get_json()
    adm_code = str(data.get('adm_code'))
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
    
    # 3. CatBoost 예측
    try:
        scores = catboost_model.predict(X_predict)
    except Exception as e:
        print(f"CatBoost 예측 오류: {e}")
        return jsonify({"error": "모델 예측 중 오류 발생."}), 500
    
    # 4. 추천 결과 생성 및 JSON 반환, 일정개수(head)
    target_df['SCORE'] = scores
    sorted_df = target_df.sort_values(by='SCORE', ascending=False)
    recommended_df = sorted_df.head(3).copy()
    
    recommended_df['DURATION'] = int(duration_days)
    recommended_df['SIDO_NM'] = sido_nm
    recommended_df['SIGUNGU_NM'] = sigungu_nm

    recommended_trips_list = recommended_df.to_dict('records')

    for trip in recommended_trips_list:
        main_area_nm = trip['VISIT_AREA_NM']
        
        # 메인 장소와 동일한 지역/테마를 가진 모든 장소 후보 필터링
        target_adm_code = trip['ADM_CODE_NUMERIC']
        target_type_cd = trip['VISIT_AREA_TYPE_CD']
        
        related_places_df = sorted_df[
            (sorted_df['ADM_CODE_NUMERIC'] == target_adm_code) & 
            (sorted_df['VISIT_AREA_TYPE_CD'] == target_type_cd) &
            (sorted_df['VISIT_AREA_NM'] != main_area_nm) 
        ]

        related_places = related_places_df['VISIT_AREA_NM'].head(5).tolist()

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