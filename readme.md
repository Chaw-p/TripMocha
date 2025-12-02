<지능형 웹 서비스 기반 전국 여행 웹 서비스>
Team Tripmocha

팀장 : 윤정
팀원 : 안유준 , 박초아

프로젝트기간 : 2025년 11월 17일 ~ 2025년 12월 19일









<db 쿼리>

CREATE TABLE tripmocha.city_county (
    id INT PRIMARY KEY AUTO_INCREMENT,
    sido VARCHAR(50) comment'시도',
    sigungu VARCHAR(50) comment'시군',
    eupmyeondong VARCHAR(50) comment'읍면동',
    latitude DECIMAL(10, 8) comment'위도',
    longitude DECIMAL(11, 8) comment'경도',
    province_id VARCHAR(50) comment'코드번호'
);
ENGINE=InnoDB
DEFAULT CHARSET=utf8mb4
COLLATE=utf8mb4_0900_ai_ci
COMMENT='전구시군도정보';


