from flask import jsonify, request, Blueprint, render_template,redirect, session
from .models import db, CityCounty,TripMain, TripMapping, TripDetail 
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
import builtins as b

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
        address = []
        x_coord = []
        y_coord = []

        # 1단계 추천 3개의 목록 (동일지역, 동일테마)
        if target_type_cd is not None:
            strict_filter = (sorted_df['ADM_CODE_NUMERIC'] == target_adm_code) & \
                            (sorted_df['VISIT_AREA_TYPE_CD'] == target_type_cd) & \
                            (sorted_df['VISIT_AREA_NM'] != main_area_nm) 
            
            related_places.extend(sorted_df[strict_filter]['VISIT_AREA_NM'].head(3).tolist())

            address.extend(sorted_df[strict_filter]['LOTNO_ADDR'].head(3).tolist())
            x_coord.extend(sorted_df[strict_filter]['X_COORD'].head(3).tolist())
            y_coord.extend(sorted_df[strict_filter]['Y_COORD'].head(3).tolist())

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

        address.extend(diverse_places_df['LOTNO_ADDR'].head(needed_count).tolist())

        x_coord.extend(diverse_places_df['X_COORD'].head(needed_count).tolist())
        y_coord.extend(diverse_places_df['Y_COORD'].head(needed_count).tolist())
        
        related_places.extend(new_places)
        print("##@@@##", related_places)
        print("##@@@##", address)
        print("##@@@##", x_coord)
        print("##@@@##", y_coord)

        while len(related_places) < 5:
            related_places.append("추가 추천 장소 (데이터 부족)")
        
        final_related_places = []
        seen_names = set()

        for i, place_name in enumerate(related_places):
            if place_name in seen_names:
                continue
                
            place_hash_id = hashlib.sha1(place_name.encode('utf-8')).hexdigest()[:10]
            
            final_related_places.append({
                "id": place_hash_id,
                "name": place_name,
                "address": address[i],
                "latitude": y_coord[i],
                "longitude": x_coord[i]
            })
            seen_names.add(place_name)

        trip['RELATED_PLACES'] = final_related_places[:5]

        session['recommended_trips'] = recommended_trips_list
        print("로그: recommended_trips_list를 세션에 저장했습니다.")
    
    print("##################",recommended_trips_list)
    return jsonify({
        "success": True,
        "recommended_trips": recommended_trips_list
    })


@schedule_bp.route("/save-draft", methods=["POST"])
def save_draft():
    print("schedule.py:save_draft():start:--------------------------");
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'status': 'error', 'message': '요청 본문(Body)이 비어있거나 JSON 형식이 아닙니다.'}), 400
     
        logged_in_user_id = session.get('user_id')
        if not logged_in_user_id:
            return jsonify({'status': 'error', 'message': '세션에서 사용자 ID를 찾을 수 없습니다 (로그인 오류 가능성).'}), 401

        trip_meta = data.get('tripMeta', {})
        selected_ids = trip_meta.get('selectedPlaceIds', [])

        # 1. TripMain 객체 생성 및 저장 준비
        new_trip_main = TripMain(
            # user_id는 인증/세션에서 가져오는 로직으로 대체해야 합니다.
            user_id=logged_in_user_id,
            title=trip_meta.get('title'),
            city=trip_meta.get('city'),
            tags=','.join(trip_meta.get('tags', [])),
            start_date=trip_meta.get('startDate'),
            end_date=trip_meta.get('endDate'),
            people=trip_meta.get('people'),
            trip_type=trip_meta.get('tripType'),
            selectedPlaceId=json.dumps(selected_ids), 
        )
        print("stage 01---")
        db.session.add(new_trip_main)
        print("stage 02---")
        # trip_no를 얻기 위해 flush를 실행합니다.
        db.session.flush() 
        print("stage 03---")
        saved_trip_no = new_trip_main.trip_no 

        print(f"saved_trip_no={saved_trip_no}")

        recommended_list = session.get('recommended_trips')
        print("@@@@@@@@@@@@@@@@@@@@@@@@@@",recommended_list)

        replated_place = [data for data in recommended_list if data.get("CONTENT_ID") == trip_meta.get("trip_no")]
        print("replated_place:@@@@@@@@@@@@@@",replated_place)

        for place_data in replated_place[0].get('RELATED_PLACES', []):

            new_trip_detail = TripDetail(
                trip_no=saved_trip_no, 
                detail_name=place_data.get('name'), # 'VISIT_AREA_NM' 사용
                address=place_data.get('address'),        # 'LOTNO_ADDR' 사용
                latitude=place_data.get('latitude', None),          # 'Y_COORD' 사용
                longitude=place_data.get('longitude', None),         # 'X_COORD' 사용
                #category=place_data.get('VISIT_AREA_TYPE_CD'), # 'VISIT_AREA_TYPE_CD' 사용
                trip_detail=place_data.get('id', None)
            )
            db.session.add(new_trip_detail)
            
        # 2. TripMapping에 초기 데이터 저장
        for index, place_id in enumerate(selected_ids):
            new_mapping = TripMapping(
                trip_no=saved_trip_no, 
                content_id=place_id,
                detail_id=None,
                day_sequence=1,       # 임시 1일차
                visit_order=index + 1 # 순서 지정
            )
            db.session.add(new_mapping)
        
        # 3. 모든 작업을 커밋하고 성공 응답
        db.session.commit()

        print("save_draft():finish:--------------------------");
        
        return jsonify({
            'status': 'success', 
            'trip_no': saved_trip_no, 
            'message': '여행 계획 초안이 성공적으로 저장되었습니다.'
        })

    except Exception as e:
        # 오류 발생 시 모든 트랜잭션을 롤백
        db.session.rollback()
        
        # 서버 콘솔에 상세 오류 출력 (디버깅용)
        import traceback
        print(f"서버 처리 중 오류 발생:\n{traceback.format_exc()}")
        print("save_draft():finish:error --------------------------");
        return jsonify({'status': 'error', 'message': '데이터베이스 저장 실패 또는 서버 처리 오류'}), 500


def clean_for_json(data):
    if isinstance(data, b.dict):
        # 딕셔너리 순회
        return {k: clean_for_json(v) for k, v in data.items()}
    elif isinstance(data, b.list):
        # 리스트 순회
        return [clean_for_json(item) for item in data]
    
    # 💡 핵심 로직: Undefined 타입 객체를 찾아서 None으로 변환
    elif str(type(data).__name__) == 'Undefined':
        return None
    
    # JSON이 이해하지 못하는 다른 모든 객체(예: ORM 모델, date 객체 등)를 문자열로 변환
    elif data is not None and not isinstance(data, (
        b.str, b.int, b.float, b.bool, b.dict, b.list
    )):
        return str(data) 
    else:
        return data

@schedule_bp.route("/view/<draftId>", methods=["GET"])
def view(draftId):
    print(f"view({draftId}):start:--------------------------");
    #recommended_list = session.pop('recommended_trips', None)
    #session['recommended_trips'] = recommended_list
    recommended_list = session.get('recommended_trips')
    print("<->" * 40)
    print(recommended_list)
    print("[-]" * 40)
    if recommended_list:
        # 💡 수정 3: 클라이언트에게 전달할 변수에 할당 (clean_for_json 적용 필요)
        cleaned_data = clean_for_json(recommended_list)
    else:
        # 세션에 데이터가 없으면 빈 리스트 또는 DB에서 초안 데이터를 로드하는 로직 필요
        cleaned_data = []
    query = ""
    url_query = request.args.get("query")
  
    if url_query is None:
        query = session.get("query", "")
    else:
        query = url_query

    session["query"] = query
    trip_record = TripMain.query.filter_by(trip_no=draftId).first()

    raw_place_id = trip_record.selectedPlaceId

    if raw_place_id and isinstance(raw_place_id, str):
        try:
            selected_place_ids_list = json.loads(raw_place_id)
        except json.JSONDecodeError:
            print("경고: selectedPlaceId가 유효한 JSON 문자열이 아닙니다.")
            selected_place_ids_list = []
    elif isinstance(raw_place_id, list):
        selected_place_ids_list = raw_place_id
    else:
        selected_place_ids_list = []
    
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
        'selectedPlaceId': selected_place_ids_list,
        'final_schedule_list_for_js' : cleaned_data
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

    # grouped_schedule = {}
    # for item in trip_schedule_data:
    #     day = item['day']
    #     if day not in grouped_schedule:
    #         grouped_schedule[day] = []
    #     grouped_schedule[day].append(item)
    # print("grouped_schedule:",grouped_schedule)
    cleaned_trip_schedule_data = clean_for_json(trip_schedule_data) 
    cleaned_trip_meta_data = clean_for_json(trip_meta_data)
    
    # meta_json_str = json.dumps(cleaned_trip_meta_data, ensure_ascii=False)
    # schedule_json_str = json.dumps(cleaned_trip_schedule_data, ensure_ascii=False)

    # safe_meta_data = quote_plus(meta_json_str)
    # safe_schedule_data = quote_plus(schedule_json_str)

    print(f"view({draftId}):finish:--------------------------");
    return render_template("schedule/schedule_view.html",
        # safe_meta_data=meta_json_str,           
        # safe_schedule_data=schedule_json_str,
        trip_meta=trip_meta_data 
        # trip_meta=cleaned_trip_meta_data, 
        # grouped_schedule=grouped_schedule, # 이 변수는 clean_for_json이 필요하다면 처리해야 함
        # query=query,
        # user_id=cleaned_trip_meta_data.get('user_id', 'Guest'), 
        # draft_id=draftId, 
        # choakey=key,
        # # 템플릿에서 | tojson 필터를 사용하는 변수명에 맞춰 수정
        # final_schedule_list_from_flask=cleaned_trip_schedule_data 
    )

# 여행 상세보기
@schedule_bp.route('/finalize', methods=['POST'])
def finalize_schedule():
    data = request.get_json()
    trip_no = request.args.get('trip_no', type=int)
    final_schedule = []

    if isinstance(data, list) and len(data) > 0:
        if isinstance(data[0], list):
            # 프론트엔드에서 [[ {place} ]] 형태로 보낸 경우
            final_schedule = data[0]
        elif isinstance(data[0], dict):
            # 프론트엔드에서 [ {place}, {place} ] 형태로 보낸 경우
            final_schedule = data
     
    # trip_no는 URL에서 가져와야 하므로, 해당 로직을 추가해야 합니다.
    if not trip_no or not final_schedule:
        return jsonify({"status": "error", "message": "필요한 데이터가 누락되었습니다. (Trip No 확인 필요)"}), 400

    try:
        for index, place_data in enumerate(final_schedule):
            content_id = place_data.get('CONTENT_ID')
            
            # --- A. TripDetail 삽입 (정수형 detail_id 획득) ---
            new_trip_detail = TripDetail(
                trip_no=trip_no, 
                detail_name=place_data.get('VISIT_AREA_NM'), # 'VISIT_AREA_NM' 사용
                address=place_data.get('LOTNO_ADDR'),        # 'LOTNO_ADDR' 사용
                latitude=place_data.get('Y_COORD', None),          # 'Y_COORD' 사용
                longitude=place_data.get('X_COORD', None),         # 'X_COORD' 사용
                category=place_data.get('VISIT_AREA_TYPE_CD'), # 'VISIT_AREA_TYPE_CD' 사용
                trip_detail=f"여행 상세 정보" 
            )
            db.session.add(new_trip_detail)
            
            db.session.flush() 
            new_detail_id = new_trip_detail.detail_id 
            print(f"로그 1: TripDetail 임시 삽입 성공. 획득한 ID: {new_detail_id}")

            mapping_record = db.session.query(TripMapping).filter_by(
                trip_no=trip_no, 
                content_id=content_id 
            ).first()

            if mapping_record:
                print(f"로그 2: TripMapping 레코드 찾음. Mapping ID: {mapping_record.mapping_id}")
                mapping_record.detail_id = new_detail_id
                mapping_record.day_sequence = 1 # 현재 데이터에 day 정보가 없으므로 1일차로 가정
                mapping_record.visit_order = index + 1
                # mapping_record.day_sequence = place_data.get('day')
                # mapping_record.visit_order = place_data.get('order')
            else:
                # 🚨 로그 3: TripMapping 레코드 못 찾음 (가장 의심되는 부분)
                print(f"로그 3: ⚠️ TripMapping 레코드 (trip_no={trip_no}, content_id={content_id}) 찾기 실패.")

        # 3. 최종 커밋
        db.session.commit()
        return jsonify({"status": "success", "message": "여행 일정이 최종 확정되었습니다."})

    except Exception as e:
        db.session.rollback()
        error_message = f"서버 처리 중 오류 발생: {type(e).__name__} - {str(e)}"
        print(error_message)
        
        return jsonify({
            "status": "error", 
            # ⚠️ str()로 감싸서 혹시 모를 비정상적인 객체 참조를 방지
            "message": f"서버 오류: {str(e)}" 
        }), 500


# 여행일정 목록
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

