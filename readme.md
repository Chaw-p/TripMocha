<db 쿼리>

CREATE TABLE tripmocha.city_county (
    id INT PRIMARY KEY AUTO_INCREMENT,
    sido VARCHAR(50) comment'시도',
    sigungu VARCHAR(50) comment'시군',
    eupmyeondong VARCHAR(50) comment'읍면동',
    li VARCHAR(50) comment'리',
    latitude DECIMAL(10, 8) comment'위도',
    longitude DECIMAL(11, 8) comment'경도',
    province_id VARCHAR(50) comment'코드번호'
);
ENGINE=InnoDB
DEFAULT CHARSET=utf8mb4
COLLATE=utf8mb4_0900_ai_ci
COMMENT='전구시군도정보';


