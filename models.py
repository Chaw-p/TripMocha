from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy() 

class CityCounty(db.Model):
    __tablename__ = 'city_county'
    id = db.Column(db.Integer, primary_key=True)
    
    sido = db.Column(db.String(50), nullable=False)        
    sigungu = db.Column(db.String(50), nullable=False)     
    eupmyeondong = db.Column(db.String(50))
    adm_code = db.Column(db.String(100))
    latitude = db.Column(db.Numeric(13, 8))
    longitude = db.Column(db.Numeric(13, 8)) 
    
    def __repr__(self):
        # sido와 sigungu를 합쳐서 지역 이름을 표시하도록 변경
        return f"<CityCounty {self.sido} {self.sigungu}>"