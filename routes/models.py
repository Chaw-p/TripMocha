from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy() 

class CityCounty(db.Model):
    __tablename__ = 'city_county'
    id = db.Column(db.Integer, primary_key=True)
    sido = db.Column(db.String(50), nullable=False)
    sigungu = db.Column(db.String(50), nullable=False)
    eupmyeondong = db.Column(db.String(50), nullable=False)
    latitude = db.Column(db.Numeric(10, 8))
    longitude = db.Column(db.Numeric(11, 8))
    adm_code = db.Column(db.String(50))
    
    def __repr__(self):
        return f"<CityCounty {self.name}>"