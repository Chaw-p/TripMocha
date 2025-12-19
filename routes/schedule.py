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
from datetime import datetime, timedelta

from functools import wraps
from flask import  url_for

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("user_id"):
            return redirect(url_for("login_bp.login_page"))
        return f(*args, **kwargs)
    return decorated_function


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
@login_required
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
    date_data = data.get('date', {})
    start_date_str = date_data.get('startDate') 
    end_date_str = date_data.get('endDate')

    try:
        if start_date_str and end_date_str:
            from datetime import datetime
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
            calculated_days = (end_date - start_date).days + 1
            duration_days = calculated_days
        else:
            duration_days = 1
        
    except Exception as e:
        print(f"WARNING: 날짜 계산 중 오류 발생, 기본값 1일 사용: {e}")
        duration_days = 1

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

    #duration_days = data.get('duration_days', 1) 
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

    #duration_days = data.get('duration_days', 1) 
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
    exclude_mask = target_df['VISIT_AREA_NM'].str.contains('호텔|아파트|오피스텔|점|펜션|화장실|PC방|모텔|주유소|충전소|병원', case=False, na=False, regex=True)
    filtered_target_df = target_df[~exclude_mask].copy()

    filtered_target_df['VISIT_AREA_NM'] = (
        filtered_target_df['VISIT_AREA_NM']
        .str.replace('주차장', '', regex=False)
        .str.replace('매표소', '', regex=False)
        .str.replace('입구', '', regex=False)
        .str.strip()  # 앞뒤 공백 제거
    )
    selected_tags = theme_tags if theme_tags else []

    # 태그별 검색 키워드 매핑
    tag_keywords = {
    'ai': '박물관|미술관|유적지|공원|해수욕장|명소', # 인기 키워드 혼합
    'mountain': '산|봉|등산|계곡|령|고개|대관령|정상',
    'sea': '해수욕장|해변|항|포구|해안|섬|바다|수변공원',
    'indoor': '박물관|미술관|전시관|기념관|과학관|실내|아쿠아리움',
    'activity': '액티비티|루지|카트|짚라인|레일바이크|랜드|월드|스키',
    'experience': '체험|농원|목장|공방|마을|테마마을|숲체험',
    'themepark': '테마파크|랜드|월드|공원|놀이동산|워터파크|유원지',
    'market': '시장|오일장|재래시장|중앙시장|풍물시장',
    'food': '맛집|식당|카페|전문점|빵집|베이커리|가든',
    'festival': '축제|행사|광장|공연장|아트센터',
    'healing': '힐링|숲|산책|휴양림|수목원|정원|식물원|둘레길',
    'photo': '사진|전망대|벽화마을|야경|출사|포토존|공원'
    }
    combined_keywords = None 
    if selected_tags:
        valid_keywords = [tag_keywords[tag] for tag in selected_tags if tag in tag_keywords]
        if valid_keywords:
            combined_keywords = "|".join(valid_keywords)

    if combined_keywords:
        tag_mask = filtered_target_df['VISIT_AREA_NM'].str.contains(combined_keywords, case=False, na=False, regex=True)
        # 점수를 대폭 가산 (지역 1순위를 유지하되 지역 내에선 1등으로)
        filtered_target_df.loc[tag_mask, 'SCORE'] += 50000
        print(f"태그 매칭 적용됨: {tag_mask.sum()}건")

    # 5. ★중요★ 가중치가 반영된 SCORE로 다시 정렬
    sorted_df = filtered_target_df.sort_values(by=['SCORE', 'VISIT_AREA_NM'], ascending=[False, True])

        #메인 후보
    diverse_main_candidates = sorted_df.drop_duplicates(
    subset=['VISIT_AREA_TYPE_CD'], 
    keep='first'
    ).copy()

    # ----------------------------------------------------
    # 1. 🚨 총 필요한 메인 후보 개수 확보 (3개 일정 * Duration)
    total_main_candidates_needed = 3 * int(duration_days)

    # 2. 🚨 전체 후보군 DataFrame 생성
    all_candidates_df = diverse_main_candidates.head(total_main_candidates_needed).copy()

    # 3. 🚨 전체 후보 리스트로 변환 (총 3*Duration 개의 딕셔너리)
    candidate_list = all_candidates_df.to_dict('records') 

    final_three_itineraries = []
    global_used_main_names = set()

    # 3개의 전체 일정을 생성 (Itinerary 1, 2, 3)
    for itinerary_index in range(1, 4):
        current_itinerary = [] 
        itinerary_used_names = set() 

        for day in range(1, int(duration_days) + 1):
            day_unique_id = f"itin/{itinerary_index}_day_{day}"
            main_candidate = None
            
            for cand in candidate_list:
                cand_name = cand['VISIT_AREA_NM']
                if cand_name not in global_used_main_names:
                    main_candidate = cand.copy()
                    global_used_main_names.add(cand_name)
                    itinerary_used_names.add(cand_name)
                    
                    # 데이터 할당
                    cand_id = hashlib.sha1(cand_name.encode('utf-8')).hexdigest()[:10]
                    main_candidate['CONTENT_ID'] = cand_id
                    main_candidate['DAY'] = day
                    main_candidate['ITINERARY_NO'] = itinerary_index
                    break
            
            # [수정] 후보가 진짜 아예 없으면 backup 장소라도 넣어서 일정이 끊기지 않게 함
            if main_candidate is None:
                # sorted_df에서 정말 아무거나 중복 안 되는 거 하나 가져옴
                backup = sorted_df[~sorted_df['VISIT_AREA_NM'].isin(itinerary_used_names)].head(1)
                if not backup.empty:
                    main_candidate = backup.iloc[0].to_dict()
                    main_candidate['DAY'] = day
                    main_candidate['ITINERARY_NO'] = itinerary_index
                    itinerary_used_names.add(main_candidate['VISIT_AREA_NM'])
                else:
                    break
            
            # 5. 기존의 서브 장소 추천 로직을 함수로 감싸거나 이 위치에 통합          
            # 메인 장소 정보 추출
            main_area_nm = str(main_candidate['VISIT_AREA_NM'])
            target_adm_code = main_candidate['ADM_CODE_NUMERIC']
            target_type_cd = main_candidate.get('VISIT_AREA_TYPE_CD') or main_candidate.get('TRAVEL_MISSION_INT')

            related_places = []
            address = []
            x_coord = []
            y_coord = []
        
            # 1단계 추천 3개 (동일지역, 동일테마)
            if target_type_cd is not None:
                strict_filter = (sorted_df['ADM_CODE_NUMERIC'] == target_adm_code) & \
                            (sorted_df['VISIT_AREA_TYPE_CD'] == target_type_cd) & \
                            (~sorted_df['VISIT_AREA_NM'].isin(itinerary_used_names)) # 
            
            selected_df = sorted_df[strict_filter].head(3)
            
            for _, row in selected_df.iterrows():
                related_places.append(row['VISIT_AREA_NM'])
                address.append(row['LOTNO_ADDR'])
                x_coord.append(row['X_COORD'])
                y_coord.append(row['Y_COORD'])
                itinerary_used_names.add(row['VISIT_AREA_NM']) # 사용 목록에 추가

            # 2단계 추천 (5개 채우기) - 기존 로직을 그대로 사용
            if len(related_places) < 4:
                needed_count = 4 - len(related_places)
            
            # 광역 필터: 동일 지역 내에서, 현재 일정(Itinerary)에서 한 번도 안 쓴 장소들만
            wide_filter = (sorted_df['ADM_CODE_NUMERIC'] == target_adm_code) & \
                          (~sorted_df['VISIT_AREA_NM'].isin(itinerary_used_names)) # [수정] 일정 내 중복 제거
            
            new_places_df = sorted_df[wide_filter].copy()
            
            # 테마 다양성 유지 로직 (기존 로직 유지)
            existing_themes = [] # 현재 날짜에 이미 뽑힌 테마들
            # (필요시 이전에 뽑힌 테마도 제외하고 싶다면 itinerary_used_themes 등을 사용 가능)

            diverse_places_df = new_places_df.drop_duplicates(subset=['VISIT_AREA_TYPE_CD'], keep='first')
            
            top_new = diverse_places_df.head(needed_count)
            for _, row in top_new.iterrows():
                related_places.append(row['VISIT_AREA_NM'])
                address.append(row['LOTNO_ADDR'])
                x_coord.append(row['X_COORD'])
                y_coord.append(row['Y_COORD'])
                itinerary_used_names.add(row['VISIT_AREA_NM']) # 사용 목록에 추가
                
                # 데이터 부족 시 채우기 (기존 로직)
                while len(related_places) < 4:
                    related_places.append("추가 추천 장소 (데이터 부족)")
                    address.append("-")
                    x_coord.append(0)
                    y_coord.append(0)
            
            # 최종 서브 장소 리스트 생성 (기존 로직)
            final_related_places = []
            for i, place_name in enumerate(related_places):
                if place_name == "추가 추천 장소 (데이터 부족)":
                    continue
                
                place_hash_id = hashlib.sha1(place_name.encode('utf-8')).hexdigest()[:10]
                final_related_places.append({
                    "id": place_hash_id,
                    "name": place_name,
                    "address": address[i],
                    "latitude": y_coord[i],
                    "longitude": x_coord[i]
                })

            # 6. 하루 일정 완성: 메인 장소를 0번째로, 서브 장소를 1~4번째로 배치합니다.
            day_schedule = [main_candidate] 
            day_schedule.extend(final_related_places[:3]) # 총 4!!개로 맞춤
            
            # 7. 메타데이터 추가 (DURATION, SIDO_NM, SIGUNGU_NM)
            for place in day_schedule:
                place['DURATION'] = int(duration_days)
                place['SIDO_NM'] = sido_nm
                place['SIGUNGU_NM'] = sigungu_nm

            # 일차 정보 저장
            current_itinerary.append({
                'day': day, 
                'day_id': day_unique_id,
                'schedule': day_schedule 
            })
                
        # 8. 전체 일정 리스트에 추가
        if current_itinerary:
            final_three_itineraries.append(current_itinerary)

     
    # 9. 🚨 recommended_trips_list 변수를 최종 결과로 사용 
    recommended_trips_list = final_three_itineraries 
    session['recommended_trips'] = recommended_trips_list
    print("로그: recommended_trips_list를 세션에 저장했습니다.")

    return jsonify({
        "success": True,
        "recommended_trips": recommended_trips_list
    })

@schedule_bp.route("/delete-detail", methods=["POST"])
def delete_detail():
    if "user_id" not in session:
        return jsonify({"success": False, "message": "로그인 필요"}), 401

    data = request.get_json()
    detail_id = data.get("detail_id")

    if not detail_id:
        return jsonify({"success": False, "message": "detail_id 없음"}), 400

    # 1️⃣ TripDetail 조회
    detail = TripDetail.query.filter_by(detail_id=detail_id).first()
    if not detail:
        return jsonify({"success": False, "message": "일정 없음"}), 404

    # 2️⃣ 소유자 체크 (TripMain.user_id 기준)
    trip = TripMain.query.filter_by(
        trip_no=detail.trip_no,
        user_id=session["user_id"]
    ).first()

    if not trip:
        return jsonify({"success": False, "message": "권한 없음"}), 403

    try:
        # 3️⃣ TripMapping 먼저 삭제
        TripMapping.query.filter_by(detail_id=detail_id).delete()

        # 4️⃣ TripDetail 삭제
        db.session.delete(detail)
        db.session.commit()

        return jsonify({"success": True})

    except Exception as e:
        db.session.rollback()
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


@schedule_bp.route("/save-draft", methods=["POST"])
def save_draft():
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
        db.session.flush() 
        print("stage 03---")
        saved_trip_no = new_trip_main.trip_no 

        print(f"saved_trip_no={saved_trip_no}")

        recommended_list = session.get('recommended_trips')

        selected_trip_id = trip_meta.get("trip_no") 
        selected_itinerary = None

        for itinerary in recommended_list:
        
            # 안전하게 접근
            if itinerary and itinerary[0] and itinerary[0].get('schedule') and itinerary[0]['schedule'][0]:
                first_place = itinerary[0]['schedule'][0]
                if first_place.get('CONTENT_ID') == selected_trip_id or first_place.get('id') == selected_trip_id:
                    selected_itinerary = itinerary
                    break

        if not selected_itinerary:
            return jsonify({'status': 'error', 'message': '선택된 여행 일정의 상세 데이터를 세션에서 찾을 수 없습니다.'}), 404

        mapping_data_list = []

        # 1. Day 순회: selected_itinerary는 Day 객체의 리스트입니다.
        for day_schedule in selected_itinerary:
            day_sequence = day_schedule.get('day') # Day 1, 2, 3...
            
            # 2. 장소 순회: schedule은 장소 객체의 리스트입니다.
            for index, place_data in enumerate(day_schedule.get('schedule', [])):
                
                # TripDetail 객체 생성
                new_trip_detail = TripDetail(
                    trip_no=saved_trip_no, 
                    detail_name=place_data.get('name') or place_data.get('VISIT_AREA_NM'), 
                    address=place_data.get('address') or place_data.get('LOTNO_ADDR'),
                    latitude=place_data.get('latitude') or place_data.get('Y_COORD'), 
                    longitude=place_data.get('longitude') or place_data.get('X_COORD'), 
                    trip_detail=place_data.get('id') or place_data.get('CONTENT_ID'),
                    day_no=day_sequence
                )
                db.session.add(new_trip_detail)
                db.session.flush() 
                new_detail_id = new_trip_detail.detail_id
                
                # TripMapping 생성을 위해 데이터를 임시 저장합니다.
                mapping_data_list.append({
                    'detail_id': new_detail_id,
                    'content_id': place_data.get('id') or place_data.get('CONTENT_ID'),
                    'day_sequence': day_sequence,
                    'visit_order': index + 1
                })

        # 3. TripMapping에 저장
        for mapping_data in mapping_data_list:
            new_mapping = TripMapping(
                trip_no=saved_trip_no, 
                content_id=mapping_data['content_id'],
                detail_id=mapping_data['detail_id'],
                day_sequence=mapping_data['day_sequence'], 
                visit_order=mapping_data['visit_order']
            )
            db.session.add(new_mapping)
        db.session.commit()
        
        return jsonify({
            'status': 'success', 
            'trip_no': saved_trip_no, 
            'message': '여행 계획 초안이 성공적으로 저장되었습니다.'
        })

    except Exception as e:
        db.session.rollback()
        
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
@login_required
def view(draftId):
    print(f"view({draftId}):start:--------------------------");
  
    recommended_list = session.get('recommended_trips')
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
    place_details = TripDetail.query.filter(TripDetail.detail_id.in_(place_ids)).all()
    place_dict = {p.detail_id: p for p in place_details} 

    print("!!place_ids:", place_ids)
    print("!!place_details count:", len(place_details))

    trip_schedule_data = []
    for mapping in trip_mappings:
        place_info = place_dict.get(mapping.detail_id)
        address_data = place_info.address if hasattr(place_info, 'address') and place_info.address is not None else "주소 정보 없음"
        if place_info:
            trip_schedule_data.append({
                'id': mapping.detail_id,
                'day': mapping.day_sequence,      
                'sequence': mapping.visit_order, 
                'name': place_info.detail_name, 
                'address': address_data 
            })
    print("****************trip_schedule_data:",trip_schedule_data)        

    grouped_schedule = {}
    for item in trip_schedule_data:
        day = item['day']
        if day not in grouped_schedule:
            grouped_schedule[day] = []
        grouped_schedule[day].append(item)

    cleaned_trip_schedule_data = clean_for_json(trip_schedule_data) 
    cleaned_trip_meta_data = clean_for_json(trip_meta_data)

    print(f"view({draftId}):finish:--------------------------");
    return render_template("schedule/schedule_view.html",
        trip_meta=cleaned_trip_meta_data, 
        grouped_schedule=grouped_schedule,
        user_id=cleaned_trip_meta_data.get('user_id', 'Guest'), 
        choakey=key,
        final_schedule_list_from_flask=cleaned_trip_schedule_data 
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
     
    if not trip_no or not final_schedule:
        return jsonify({"status": "error", "message": "필요한 데이터가 누락되었습니다. (Trip No 확인 필요)"}), 400

    try:
        for index, place_data in enumerate(final_schedule):
            content_id = place_data.get('CONTENT_ID')
            
            new_trip_detail = TripDetail(
                trip_no=trip_no, 
                detail_name=place_data.get('VISIT_AREA_NM'), 
                address=place_data.get('LOTNO_ADDR'),        
                latitude=place_data.get('Y_COORD', None),         
                longitude=place_data.get('X_COORD', None),        
                category=place_data.get('VISIT_AREA_TYPE_CD'), 
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
            else:
                print(f"로그 3: ⚠️ TripMapping 레코드 (trip_no={trip_no}, content_id={content_id}) 찾기 실패.")

        db.session.commit()
        return jsonify({"status": "success", "message": "여행 일정이 최종 확정되었습니다."})

    except Exception as e:
        db.session.rollback()
        error_message = f"서버 처리 중 오류 발생: {type(e).__name__} - {str(e)}"
        print(error_message)
        
        return jsonify({
            "status": "error", 
            "message": f"서버 오류: {str(e)}" 
        }), 500


# 여행일정 목록
@schedule_bp.route("/list", methods=["GET"])
@login_required
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

