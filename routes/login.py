import os
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, session, current_app
from flask_cors import CORS
from google import genai
from google.genai.errors import APIError
import time
import smtplib
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formataddr
import random

# Blueprint 정의
login_bp = Blueprint('login_bp', __name__)
api_bp = Blueprint('api_bp', __name__)

auth_codes = {}

def send_email_utf8(to_email, name, auth_code):
    smtp_server = "smtp.gmail.com"
    smtp_port = 587

    # Gmail 계정 정보
    smtp_user = "ayj0519@gmail.com"
    smtp_password = "lhccakvpnvcfpsve"

    # 이메일 본문 (UTF-8)
    body = f"""
안녕하세요 {name}님,

TripMocha 비밀번호 재설정 인증번호는

인증번호: {auth_code}

입니다.
3분 안에 입력해주세요.
"""
    
    print("=== EMAIL BODY START ===")
    for i, ch in enumerate(body):
        print(i, repr(ch))
    print("=== EMAIL BODY END ===")

    # UTF-8 본문
    msg = MIMEText(body, "plain", "utf-8")

    # 제목 UTF-8
    msg["Subject"] = "TripMocha Verification Code"

    # From UTF-8 인코딩
    msg["From"] = smtp_user

    msg["To"] = to_email

    server = smtplib.SMTP(smtp_server, smtp_port)
    server.starttls()
    server.login(smtp_user, smtp_password)
    server.sendmail(smtp_user, [to_email], msg.as_string())
    server.quit()

@api_bp.route('/api/send_auth_code', methods=['POST'])
def send_auth_code():
    email = request.form.get('email')
    user_id = request.form.get('user_id')
    name = request.form.get('name')

    print("받은 데이터:", email, user_id, name)

    if not email:
        return jsonify({"success": False, "message": "이메일이 필요합니다."}), 400

    auth_code = str(random.randint(100000, 999999))
    auth_codes[email] = auth_code

    try:
        send_email_utf8(email, name, auth_code)
        print("이메일 전송 성공:", email, auth_code)
        return jsonify({"success": True})

    except Exception as e:
        print("이메일 전송 오류:", e)
        return jsonify({"success": False, "message": "메일 발송 실패"}), 500
    
    
@api_bp.route('/api/verify_auth_code', methods=['POST'])
def verify_auth_code():
    email = request.form.get('email')
    user_input_code = request.form.get('auth_code')

    real_code = auth_codes.get(email)

    if not real_code:
        return jsonify({"success": False, "message": "인증번호가 없습니다. 다시 요청해주세요."})

    if user_input_code == real_code:
        return jsonify({"success": True, "message": "인증 성공!"})
    else:
        return jsonify({"success": False, "message": "인증번호가 일치하지 않습니다."})
    
# ----------------------------------------------------
# C. Gemini API 키 설정 및 보안 강화
# ----------------------------------------------------
# NOTE: os.getenv를 사용하여 환경 변수에서 안전하게 키를 불러오는 방식으로 변경했습니다.
# 실제 환경 변수 설정이 필요합니다 (예: .env 파일 사용).
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyCSm8j9_SnGJVdoHvyc1BKpe_1hAh5kVRw")

# ----------------------------------------------------
# A. 사용자 인증 및 페이지 렌더링 라우팅
# ----------------------------------------------------

# 1. 메인 페이지 (Root URL) 라우팅: /
@login_bp.route('/')
def home():
    return render_template('login/login.html')

@login_bp.route('/login')
def login_page():
    return render_template('login/login.html')

@login_bp.route('/join')
def join_page():
    return render_template('login/join.html')

@login_bp.route('/find_id')
def find_id_page():
    return render_template('login/find_id.html')

@login_bp.route('/find_password')
def find_password():
    return render_template('login/find_password.html')

# === index.html 메인 페이지 (LOGIN 후 이동) ===
@login_bp.route('/index')
def index_page():
    return render_template('index.html')

# ----------------------------------------------------
# B. 폼 데이터 처리 라우팅 (POST)
# ----------------------------------------------------

# 7. 로그인 폼 처리 라우트: /login (POST 요청)
@login_bp.route('/login', methods=['POST'])
def process_login():
    print("=== 로그인 라우트 실행됨 ===")  # 추가

    user_id = request.form.get("user_id")
    print("받은 아이디:", user_id)  # 추가

    session["user_id"] = user_id
    print("세션 저장됨:", session.get("user_id"))  # 추가

    return redirect(url_for('login_bp.index_page'))

@login_bp.route('/index')
def travel_plan_ui():
    return render_template('index.html')




@login_bp.route('/find_id_process', methods=['POST'])
def find_id_process():
    # TODO: 아이디 찾기 로직 구현 필요
    return jsonify({"message": "아이디 찾기 처리 완료 (로직 구현 필요)"})


@login_bp.route('/find_password_process', methods=['POST'])
def find_password_process():
    # TODO: 비밀번호 찾기 로직 구현 필요
    return jsonify({"message": "비밀번호 찾기 처리 완료 (로직 구현 필요)"})

# 8. 회원가입 폼 처리 라우트: /signup (POST 요청)
@login_bp.route('/signup', methods=['POST'])
def process_signup():
    """회원가입 폼 제출을 처리하고 성공 시 로그인 페이지로 리다이렉트합니다."""
    data = request.form
    
    # TODO: DB 저장 로직 구현 필요
    print(f"회원가입 데이터 수신: {data.get('user_id')}")

    return redirect(url_for('.login_page'))

@login_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login_bp.login_page'))



# ----------------------------------------------------
# B-1. 아이디 중복 확인 라우팅 (AJAX용)
# ----------------------------------------------------
# NOTE: 이 함수를 routes/models.py나 별도의 services/auth.py로 분리하는 것이 좋습니다.

def check_id_exists_in_db(user_id):
    """
    Placeholder 함수: 실제 데이터베이스에서 해당 user_id가 존재하는지 확인하는 함수
    """
    # 예시: 'admin', 'testuser' 아이디는 이미 존재한다고 가정
    return user_id in ['admin', 'testuser']

@login_bp.route('/check_duplicate', methods=['POST'])
def check_duplicate():
    """
    프론트엔드의 AJAX 요청을 받아 아이디 중복 여부를 확인하고 JSON 응답을 반환합니다.
    """
    user_id = request.form.get('user_id') 
    
    if not user_id:
        return jsonify({'error': '아이디를 입력해 주세요.'}), 400

    is_duplicate = check_id_exists_in_db(user_id)
    
    return jsonify({
        'is_duplicate': is_duplicate 
    })


# ----------------------------------------------------
# C. Gemini API 호출 라우팅 (여행 계획 생성)
# ----------------------------------------------------

# XML_PROMPT_TEMPLATE = """
# 당신은 오직 XML 형식의 데이터만을 출력해야 합니다. 추가적인 설명이나 서론/결론 문구를 절대 포함하지 마세요.
# {destination_str} 여행을 {duration_str} 동안 {date_str}부터 2명(남,여 각 1명) 이 여행하고 싶은데 여행 코스를 작성해줘
# 작성된 결과는 다음 XML 문서의 {{}}안에 작성해줘. 여행코스 태그는 여행 일자에 따라서 반복해서 작성해줘
# 숙소 태그에 내용이 없으면 "내용없음"으로 출력해줘

# <여행가이드>
#     <여행코스>
#         <일자>{{여행일자}}</일자>
#         <장소>{{장소}}</장소>
#         <숙소>{{숙소}}</숙소>
#         <비용>{{비용}}</비용>
#         <지도위치>{{위도}},{{경도}}</지도위치>
#         <상세설명>
#             <오전>{{상세설명}}</오전>
#             <점심>{{상세설명}}</점심>
#             <오후>{{상세설명}}</오후>
#         </상세설명>
#     </여행코스>
# </여행가이드>
# """

# @login_bp.route('/api/travel_plan', methods=['POST'])
# def get_travel_plan():
#     """프론트엔드 요청을 받아 Gemini API를 호출하고 XML 결과를 반환합니다."""
    
#     try:
#         data = request.json
#         date_query = data.get('startDate', '2025년 12월 1일')
#         duration_query = data.get('duration', '1박 2일')
#         destination_query = data.get('destination', '파주')
        
#         if not destination_query or not date_query or not duration_query:
#             return jsonify({'xml_data': "<여행가이드><error>INVALID_INPUT: 지역, 날짜 또는 기간 정보가 누락되었습니다.</error></여행가이드>"}), 400
    
#     except Exception:
#         return jsonify({'xml_data': "<여행가이드><error>INVALID_REQUEST: 요청 JSON 형식이 잘못되었습니다.</error></여행가이드>"}), 400
    
#     xml_result = generate_gemini_travel_plan(date_query, destination_query, duration_query)
    
#     return jsonify({'xml_data': xml_result})


# def generate_gemini_travel_plan(date_str: str, destination_str: str, duration_str: str) -> str:
#     """Gemini API를 호출하여 XML 형식의 여행 계획을 생성합니다."""
    
#     prompt = XML_PROMPT_TEMPLATE.format(
#         date_str=date_str, 
#         destination_str=destination_str,
#         duration_str=duration_str
#     )
    
#     try:
#         # NOTE: 이 함수를 별도의 services/gemini_service.py로 분리하는 것이 좋습니다.
#         client = genai.Client(api_key=GEMINI_API_KEY) 
#         model = 'gemini-2.5-flash'
        
#         response = client.models.generate_content(
#             model=model,
#             contents=prompt,
#         )
        
#         return response.text

#     except APIError as e:
#         return f"<여행가이드><error>API_ERROR: {e}</error></여행가이드>"
#     except Exception as e:
#         return f"<여행가이드><error>UNKNOWN_ERROR: {e}</error></여행가이드>"