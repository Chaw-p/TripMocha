
from datetime import datetime
import json
from sqlalchemy import exc

from .models import db, TripMain , TripMapping 

def save_data_to_database(trip_meta, search_criteria, trip_schedule_plan):
    """
    TripMain 모델을 사용하여 DB에 여행 초안을 저장하고 trip_id를 반환합니다.
    
    Args:
        trip_meta (dict): 여행 경로 및 메타데이터 (예: selectedPlaceIds)
        search_criteria (dict): 초기 검색 조건 (예: city, start_date, people)
        
    Returns:
        int: 새로 생성된 trip_id
    """
    
    date_data = search_criteria.get('date', {}) 
    start_date_val = date_data.get('startDate') 
    end_date_val = date_data.get('endDate')

    start_date_obj = None
    end_date_obj = None

    if start_date_val and end_date_val:
        try:
            start_date_obj = datetime.strptime(start_date_val, '%Y-%m-%d').date()
            end_date_obj = datetime.strptime(end_date_val, '%Y-%m-%d').date()
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid date format for start/end date. Expected YYYY-MM-DD. Error: {e}")
        
    # 2. TripMain 모델 인스턴스 생성 및 데이터 매핑
    city_name = trip_meta.get('city', '').strip()
    tags_list = trip_meta.get('tags', [])
    tags_string = ",".join(tags_list) 
    selected_places_list = trip_meta.get('selectedPlaceIds', [])
    
    people_count = trip_meta.get('people', 0) 
    trip_type_value = trip_meta.get('trip_type', '일반') 
    selectedPlaceId_string = ",".join(trip_meta.get('selectedPlaceIds', []))

    try: 
        new_trip = TripMain(
            user_id = '1234', 
            title = trip_meta.get('title', '제목 없음'),
            city = city_name, 
            tags = tags_string,
            start_date = start_date_obj,
            end_date = end_date_obj,
            people = people_count,
            trip_type = trip_type_value,
            
            selectedPlaceId = json.dumps(trip_meta.get('selectedPlaceIds')) if trip_meta.get('selectedPlaceIds') else None
        )
    
        db.session.add(new_trip)
        db.session.flush()
        trip_no = new_trip.trip_no

        for item in trip_schedule_plan:
            new_mapping = TripMapping(
                trip_no = trip_no,
                detail_id = item['id'],
                day_sequence = item['day'],
                visit_order = item['order']
            )
            db.session.add(new_mapping)
        
        db.session.commit()
        return trip_no
    except (exc.SQLAlchemyError, Exception) as e:
        # 오류 발생 시 롤백
        db.session.rollback()
        print(f"DB 저장 중 오류 발생: {e}")
        raise e

   