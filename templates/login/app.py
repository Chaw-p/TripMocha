import os
from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_cors import CORS
from google import genai
from google.genai.errors import APIError
import random
import time

# Flask 애플리케이션 초기화
app = Flask(__name__)
CORS(app) # CORS 허용

# ----------------------------------------------------
# C. Gemini API 키 설정 및 보안 강화
# ----------------------------------------------------
# 중요: API 키를 코드에 직접 하드코딩하지 않고 환경 변수에서 불러옵니다.
# 실제 배포 시에는 'your_gemini_api_key' 대신 환경 변수를 설정해야 합니다.
GEMINI_API_KEY = "AIzaSyCSm8j9_SnGJVdoHvyc1BKpe_1hAh5kVRw"

# ----------------------------------------------------
# A. 사용자 인증 및 페이지 렌더링 라우팅
# ----------------------------------------------------

# 1. 메인 페이지 (Root URL) 라우팅: http://127.0.0.1:5000/
@app.route('/')
def home():
    """메인 페이지에서는 로그인 페이지를 렌더링합니다."""
    # 실제 프로젝트 구조에 따라 경로를 확인하세요.
    return render_template('user/login.html')

# 2. 로그인 페이지 라우팅 (GET): http://127.0.0.1:5000/login
@app.route('/login')
def login_page():
    return render_template('user/login.html')

# 3. 회원가입 페이지 라우팅: http://127.0.0.1:5000/join
@app.route('/join')
def join_page():
    # 프론트엔드 파일명(signup.html)과 일치하도록 템플릿 파일명에 주의하세요.
    # 현재는 'user/join.html'로 가정하고 유지합니다.
    return render_template('user/join.html')

# 4. 아이디 찾기 페이지 라우팅: http://127.0.0.1:5000/find_id
@app.route('/find_id')
def find_id_page():
    return render_template('user/find_id.html')

# 5. 비밀번호 찾기 페이지 라우팅: http://127.0.0.1:5000/find_password
@app.route('/find_password')
def find_password_page():
    return render_template('user/find_password.html')

# 6. 여행 계획 메인 UI 페이지 라우팅: http://127.0.0.1:5000/travel
@app.route('/travel')
def travel_plan_ui():
    """로그인 성공 후 접속하는 메인 여행 계획 UI를 렌더링합니다."""
    return render_template('user/travel.html')



# ----------------------------------------------------
# B. 폼 데이터 처리 라우팅 (POST)
# ----------------------------------------------------

# 7. 로그인 폼 처리 라우트: /login (POST 요청)
@app.route('/login', methods=['POST'])
def process_login():
    """로그인 폼 제출을 처리하고 성공 시 메인 페이지로 리다이렉트합니다."""
    #  필수 구현: request.form.get('user_id'), request.form.get('password')를 사용하여
    # DB 인증 로직을 구현해야 합니다.
    # 현재는 인증에 성공했다고 가정하고 '/travel'로 리다이렉트합니다.
    return redirect(url_for('travel_plan_ui'))


@app.route('/find_id_process', methods=['POST'])
def find_id_process():
    #  필수 구현: 이름, 생년월일 등의 정보를 받아 DB에서 아이디를 찾아 반환하는 로직 구현
    return jsonify({"message": "아이디 찾기 처리 완료 (로직 구현 필요)"})


@app.route('/find_password_process', methods=['POST'])
def find_password_process():
    #  필수 구현: 아이디, 이름 등의 정보를 받아 비밀번호 재설정 로직 구현
    # 인증 완료 후 이 페이지로 넘어와 비밀번호 재설정을 처리하게 됩니다.
    return jsonify({"message": "비밀번호 찾기 처리 완료 (로직 구현 필요)"})

# 8. 회원가입 폼 처리 라우트: /signup (POST 요청)
@app.route('/signup', methods=['POST'])
def process_signup():
    """회원가입 폼 제출을 처리하고 성공 시 로그인 페이지로 리다이렉트합니다."""
    data = request.form
    
    #  필수 구현:
    # 1. 비밀번호 해싱 (예: bcrypt)
    # 2. 데이터베이스에 사용자 정보 (data['user_id'], data['password'], data['name'] 등) 저장
    
    print(f"회원가입 데이터 수신: {data.get('user_id')}")

    # 성공했다고 가정하고 로그인 페이지로 리다이렉트
    return redirect(url_for('login_page'))


# ----------------------------------------------------
# B-1. 아이디 중복 확인 라우팅 (AJAX용)
# ----------------------------------------------------

def check_id_exists_in_db(user_id):
    """
     Placeholder 함수: 실제 데이터베이스에서 해당 user_id가 존재하는지 확인하는 함수
     필수 구현: 이 부분을 실제 DB 연결 및 SELECT 쿼리 로직으로 반드시 변경해야 합니다.
    """
    # 예시: 'admin', 'testuser' 아이디는 이미 존재한다고 가정
    return user_id in ['admin', 'testuser']

@app.route('/check_duplicate', methods=['POST'])
def check_duplicate():
    """
    프론트엔드의 AJAX 요청을 받아 아이디 중복 여부를 확인하고 JSON 응답을 반환합니다.
    """
    user_id = request.form.get('user_id')
    
    if not user_id:
        return jsonify({'error': '아이디를 입력해 주세요.'}), 400

    # 데이터베이스 중복 확인 함수 호출
    is_duplicate = check_id_exists_in_db(user_id)
    
    # JSON 응답 반환
    return jsonify({
        'is_duplicate': is_duplicate  # True면 중복, False면 사용 가능
    })


# ----------------------------------------------------
# C. Gemini API 호출 라우팅 (여행 계획 생성)
# ----------------------------------------------------

XML_PROMPT_TEMPLATE = """
당신은 오직 XML 형식의 데이터만을 출력해야 합니다. 추가적인 설명이나 서론/결론 문구를 절대 포함하지 마세요.
{destination_str} 여행을 {duration_str} 동안 {date_str}부터 2명(남,여 각 1명) 이 여행하고 싶은데 여행 코스를 작성해줘
작성된 결과는 다음 XML 문서의 {{}}안에 작성해줘. 여행코스 태그는 여행 일자에 따라서 반복해서 작성해줘
숙소 태그에 내용이 없으면 "내용없음"으로 출력해줘

<여행가이드>
    <여행코스>
        <일자>{{여행일자}}</일자>
        <장소>{{장소}}</장소>
        <숙소>{{숙소}}</숙소>
        <비용>{{비용}}</비용>
        <지도위치>{{위도}},{{경도}}</지도위치>
        <상세설명>
            <오전>{{상세설명}}</오전>
            <점심>{{상세설명}}</점심>
            <오후>{{상세설명}}</오후>
        </상세설명>
    </여행코스>
</여행가이드>
"""

@app.route('/api/travel_plan', methods=['POST'])
def get_travel_plan():
    """프론트엔드 요청을 받아 Gemini API를 호출하고 XML 결과를 반환합니다."""
    
    if GEMINI_API_KEY == "your_gemini_api_key_placeholder":
          return jsonify({'xml_data': "<여행가이드><error>API_KEY_MISSING: API 키가 설정되지 않았습니다.</error></여행가이드>"}), 500

    try:
        data = request.json
        date_query = data.get('startDate', '2025년 12월 1일')
        duration_query = data.get('duration', '1박 2일')
        destination_query = data.get('destination', '파주')
        
        if not destination_query or not date_query or not duration_query:
            return jsonify({'xml_data': "<여행가이드><error>INVALID_INPUT: 지역, 날짜 또는 기간 정보가 누락되었습니다.</error></여행가이드>"}), 400
    
    except Exception:
        return jsonify({'xml_data': "<여행가이드><error>INVALID_REQUEST: 요청 JSON 형식이 잘못되었습니다.</error></여행가이드>"}), 400
    
    print(f"[{destination_query}, {date_query} 시작, {duration_query} 기간] 여행 계획 생성 요청 접수.")

    xml_result = generate_gemini_travel_plan(date_query, destination_query, duration_query)
    
    return jsonify({'xml_data': xml_result})


def generate_gemini_travel_plan(date_str: str, destination_str: str, duration_str: str) -> str:
    """Gemini API를 호출하여 XML 형식의 여행 계획을 생성합니다."""
    
    # 이 함수 내부에서는 API 키가 설정되어 있다고 가정합니다. (get_travel_plan에서 이미 검사)
    
    prompt = XML_PROMPT_TEMPLATE.format(
        date_str=date_str, 
        destination_str=destination_str,
        duration_str=duration_str
    )
    
    try:
        client = genai.Client(api_key=GEMINI_API_KEY) 
        model = 'gemini-2.5-flash'
        
        response = client.models.generate_content(
            model=model,
            contents=prompt,
        )
        
        return response.text

    except APIError as e:
        return f"<여행가이드><error>API_ERROR: {e}</error></여행가이드>"
    except Exception as e:
        return f"<여행가이드><error>UNKNOWN_ERROR: {e}</error></여행가이드>"
    
# ----------------------------------------------------
# D. 비밀번호 찾기 (휴대전화 인증) 라우팅
# ----------------------------------------------------

# 💡 인증번호 임시 저장소 (전화번호를 키로 사용)
AUTH_CODES = {} 

@app.route('/api/send_auth_code', methods=['POST'])
def send_auth_code():
    data = request.form
    phone_number = data.get('phone_number')
    
    if not phone_number:
         return jsonify({"success": False, "message": "휴대전화 번호를 입력해주세요."}), 400

    # 1.  실제 DB: user_id와 name, phone_number가 모두 일치하는 사용자가 있는지 확인해야 합니다.
    #    (현재는 생략)

    # 2. [테스트용 코드]: 인증번호를 '999999'로 고정합니다.
    auth_code = "999999" 
    
    # 3. 인증번호 저장 (3분 후 만료 시뮬레이션)
    expiration_time = time.time() + (3 * 60)
    AUTH_CODES[phone_number] = {"code": auth_code, "expires": expiration_time}
    
    # 4.  실제 SMS 발송 로직은 실행하지 않습니다.
    
    print(f"DEBUG: {phone_number}로 테스트 코드 {auth_code}가 발송되었다고 가정합니다.")
    
    return jsonify({"success": True, "message": "테스트 인증번호 발송 완료"})


@app.route('/api/verify_auth_code', methods=['POST'])
def verify_auth_code():
    """클라이언트로부터 인증번호를 받아 저장된 코드와 비교하여 검증합니다."""
    data = request.form
    phone_number = data.get('phone_number')
    user_input_code = data.get('auth_code')
    
    stored_data = AUTH_CODES.get(phone_number)
    
    if not stored_data:
        return jsonify({"success": False, "message": "인증번호를 다시 요청해주세요. (코드 만료/미요청)"})
    
    # 1. 만료 시간 확인
    if time.time() > stored_data["expires"]:
        del AUTH_CODES[phone_number] # 만료된 코드는 삭제
        return jsonify({"success": False, "message": "인증 시간이 만료되었습니다. 다시 요청해주세요."})
        
    # 2. 코드 일치 확인
    if user_input_code == stored_data["code"]:
        del AUTH_CODES[phone_number] # 성공했으니 코드 삭제
        return jsonify({"success": True, "message": "인증 성공! 비밀번호 재설정 페이지로 이동합니다."})
    else:
        return jsonify({"success": False, "message": "인증번호가 일치하지 않습니다."})


# -----------------------------------------------
# 서버 실행
if __name__ == '__main__':
    app.run(debug=True)