from flask import jsonify, request, Blueprint, render_template,redirect, session
from .models import db, CityCounty,TripMain, TripMapping 
from dotenv import load_dotenv
import os
import pickle
from catboost import CatBoostRegressor
import pandas as pd
import numpy as np
import hashlib
import json
from .database import save_data_to_database
from urllib.parse import quote_plus

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

# @schedule_bp.route("/view", methods=["POST"])
# def tripok():
#     # title = request.form.get("trip-title")
#     # city  = request.form.get("trip-city")
#     # duration  = request.form.get("trip-duration")
#     # startDate  = request.form.get("trip-startDate")
#     # endDate  = request.form.get("trip-endDate")


#     return render_template("schedule/schedule_view.html")


# 특징생성함수
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
    target_df['VISIT_AREA_NM'].str.contains('점', case=False, na=False) | \
    target_df['VISIT_AREA_NM'].str.contains('펜션', case=False, na=False)
    filtered_target_df = target_df[~exclude_mask].copy()
    sorted_df = filtered_target_df.sort_values(by='SCORE', ascending=False)

    diverse_main_candidates = sorted_df.drop_duplicates(
    subset=['VISIT_AREA_TYPE_CD'], 
    keep='first'
    ).copy()
    
    recommended_df = diverse_main_candidates.head(3).copy()
    
    recommended_df['DURATION'] = int(duration_days)
    recommended_df['SIDO_NM'] = sido_nm
    recommended_df['SIGUNGU_NM'] = sigungu_nm

    recommended_trips_list = recommended_df.to_dict('records')

    # 메인 장소 추천 후 반복문
    
    for trip in recommended_trips_list:
        main_area_nm = str(trip['VISIT_AREA_NM'])
        target_adm_code = trip['ADM_CODE_NUMERIC']
        target_type_cd = trip.get('VISIT_AREA_TYPE_CD') or trip.get('TRAVEL_MISSION_INT')
        trip['CONTENT_ID'] = hashlib.sha1(main_area_nm.encode('utf-8')).hexdigest()[:10]
        print("현재 처리 중인 Trip 데이터:", trip)
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
        
        final_related_places = []
        seen_names = set()

        for place_name in related_places:
            if place_name in seen_names:
                continue
                
            place_hash_id = hashlib.sha1(place_name.encode('utf-8')).hexdigest()[:10]
            
            final_related_places.append({
                "id": place_hash_id,
                "name": place_name
            })
            seen_names.add(place_name)

        trip['RELATED_PLACES'] = final_related_places[:5]
    
    return jsonify({
        "success": True,
        "recommended_trips": recommended_trips_list
    })


@schedule_bp.route("/save-draft", methods=["POST"])
def save_draft():
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'status': 'error', 'message': '요청 본문(Body)이 비어있거나 JSON 형식이 아닙니다.'}), 400

        trip_meta = data.get('tripMeta')
        search_criteria = data.get('searchCriteria')
        trip_schedule_plan = data.get('schedule_plan', [])

        try:
            trip_no = save_data_to_database(trip_meta, search_criteria, trip_schedule_plan)
        except Exception as db_err:
            print("데이터베이스 저장 오류:", str(db_err))
            return jsonify({
                'status': 'error', 
                'message': '데이터베이스 저장 중 오류가 발생했습니다.'
            }), 500
    
        # DB 저장 및 ID 획득 가정
        
        # JSON 응답으로 ID 반환
        return jsonify({
            'status': 'success',
            'trip_no' : trip_no,
            'message': '여행 계획 초안이 성공적으로 저장되었습니다.'
        })

    except Exception as e:
        print("서버 처리 중 오류 발생:", str(e))
        return jsonify({'status': 'error', 'message': f'서버 처리 오류: {str(e)}'}), 500
    

@schedule_bp.route("/view/<draftId>", methods=["GET"])
def view(draftId):
  
    query = ""
    url_query = request.args.get("query")
  
    if url_query is None:
        query = session.get("query", "")
    else:
        query = url_query

    # 세션에 값이 있을경우는 파라메터 값 없을 경우는 빈값을 다시 넣는다.
    session["query"] = query
    trip_record = TripMain.query.filter_by(trip_no=draftId).first()

    if trip_record is None:
        print("db에 id 없음")
        
        trip_meta_data = {}
    else:
        trip_meta_data = {
            'trip_no': trip_record.trip_no, 
            'user_id': trip_record.user_id, 
            'title': trip_record.title, 
            'city': trip_record.city,
            'tags': trip_record.tags.split(',') if trip_record.tags else [],
            'start_date': trip_record.start_date.strftime('%Y-%m-%d') if trip_record.start_date else '',
            'end_date': trip_record.end_date.strftime('%Y-%m-%d') if trip_record.end_date else '',    
            'people': trip_record.people,
            'trip_type': trip_record.trip_type, 
            'selectedPlaceId': trip_record.selectedPlaceId if trip_record.selectedPlaceId is not None else []
        }
    trip_mappings = TripMapping.query.filter_by(trip_no=draftId).order_by(
    TripMapping.day_sequence, 
    TripMapping.visit_order
    ).all()

    place_ids = [m.detail_id for m in trip_mappings]
    place_details = TripMapping.query.filter(TripMapping.detail_id.in_(place_ids)).all()
    place_dict = {p.detail_id: p for p in place_details} # 딕셔너리로 변환

    trip_schedule_data = []
    for mapping in trip_mappings:
        place_info = place_dict.get(mapping.detail_id)
        address_data = place_info.address if hasattr(place_info, 'address') and place_info.address is not None else "주소 정보 없음"
        if place_info:
            trip_schedule_data.append({
                'id': mapping.detail_id,
                'day': mapping.day_sequence,      
                'sequence': mapping.visit_order, 
                'name': place_info.place_name, 
                'address': address_data 
            })

    meta_json_str = json.dumps(trip_meta_data, ensure_ascii=False)
    schedule_json_str = json.dumps(trip_schedule_data, ensure_ascii=False) 
    safe_meta_data = quote_plus(meta_json_str)
    safe_schedule_data = quote_plus(schedule_json_str)
    print(f"Flask에서 전달되는 Meta Data: {trip_meta_data}")
     
    return render_template("schedule/schedule_view.html",safe_meta_data=safe_meta_data, 
    safe_schedule_data=safe_schedule_data,
    trip_meta=trip_meta_data,search_query=query, trip_schedule=trip_schedule_data, user_id=trip_meta_data.get('user_id', 'Guest'), draft_id=draftId , choakey=key)


@schedule_bp.route("/list", methods=["GET"])
def list():
    query = ""
    url_query = request.args.get("query")
  
    if url_query is None:
        query = session.get("query", "")
    else:
        query = url_query
    
    session["query"] = query
    current_user_id = session.get('user_id', 'Guest')
    trip_records = TripMain.query.filter_by(user_id=current_user_id).order_by(
        TripMain.trip_no.desc()).all()
    
    trip_list_data = []
    for record in trip_records:
        trip_list_data.append({
            'trip_no': record.trip_no, 
            'title': record.title, 
            'city': record.city,
            'tags': record.tags.split(',') if record.tags else [],
            'start_date': record.start_date.strftime('%Y-%m-%d') if record.start_date else '',
            'end_date': record.end_date.strftime('%Y-%m-%d') if record.end_date else '', 
            'duration': (record.end_date - record.start_date).days + 1 if record.start_date and record.end_date else 0, 
            'people': record.people,
            'user_id': record.user_id,
        })

    return render_template(
        "schedule/schedule_list.html", 
        trips=trip_list_data, 
        search_query=query, 
        current_user_id=current_user_id
    )

