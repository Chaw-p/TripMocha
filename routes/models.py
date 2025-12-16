from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy() 

# 여행일정 만들기 지역 검색 db
class CityCounty(db.Model):
    __tablename__ = 'trip_city'
    id = db.Column(db.Integer, primary_key=True)
    sido = db.Column(db.String(50), nullable=False)
    sigungu = db.Column(db.String(50), nullable=False)
    eupmyeondong = db.Column(db.String(50), nullable=False)
    latitude = db.Column(db.Numeric(10, 8))
    longitude = db.Column(db.Numeric(11, 8))
    adm_code = db.Column(db.String(50))
    
    def __repr__(self):
        return f"<CityCounty {self.name}>"
    
class TripMain(db.Model):
    __tablename__ = 'trip_main'
    trip_no = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.String(50))
    title = db.Column(db.String(200))
    city = db.Column(db.String(100))
    tags = db.Column(db.String(300))
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    people = db.Column(db.Integer)
    trip_type = db.Column(db.String(100))
    selectedPlaceId = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=db.func.now())
    
    def __repr__(self):
        return f"<TripMain {self.title}>"
    
class TripMapping(db.Model):
    __tablename__ = 'trip_mapping'
    mapping_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    trip_no = db.Column(db.Integer, db.ForeignKey('trip_main.trip_no'))
    detail_id = db.Column(db.String(100), db.ForeignKey('trip_de.trip_no'))
    day_sequence = db.Column(db.Integer)
    visit_order = db.Column(db.Integer)
   
    def __repr__(self):
        return f"<TripMapping {self.mapping_id}>"