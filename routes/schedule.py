from flask import jsonify, request, Blueprint, render_template
from routes.models import db, CityCounty 


schedule_bp = Blueprint("schedule", __name__, url_prefix="/schedule")

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
    
    # 템플릿에 전달할 때, city_name을 sido와 sigungu를 합친 이름으로 만듭니다.
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

@schedule_bp.route("/view", methods=["GET"])
def view():
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
    
    # 템플릿에 전달할 때, city_name을 sido와 sigungu를 합친 이름으로 만듭니다.
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


    return render_template("schedule/schedule_view.html", destinations=processed_destinations)

@schedule_bp.route("/list", methods=["GET"])
def list():
    return render_template("schedule/schedule_list.html")