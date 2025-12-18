import os
from flask import (
    Blueprint,
    render_template,
    request,
    jsonify,
    redirect,
    url_for,
    session,
    current_app,
)
from flask_cors import CORS
from google import genai
from google.genai.errors import APIError
import time

# import smtplib
# from email.mime.text import MIMEText
# from email.header import Header
# from email.utils import formataddr
import random
from flask import g
import bcrypt
import traceback
import pymysql
from dotenv import load_dotenv

# from email.message import EmailMessage
# from email.policy import SMTPUTF8
from flask_mail import Message
from extensions import mail

from datetime import datetime, timedelta


load_dotenv()


def mask_user_id(user_id: str) -> str:
    if len(user_id) <= 2:
        return user_id[0] + "*"
    return user_id[0] + "*" * (len(user_id) - 2) + user_id[-1]


# -------------------------------------------------
# MySQL 직접 연결용 함수 (get_db)
# -------------------------------------------------
def get_db():
    if "db" not in g:
        g.db = pymysql.connect(
            host="192.168.60.133",
            user="tripmocha",
            password="ezen",
            database="tripmocha",
            charset="utf8mb4",
            cursorclass=pymysql.cursors.Cursor,
        )
    return g.db


# Blueprint 정의
login_bp = Blueprint("login_bp", __name__)
api_bp = Blueprint("api_bp", __name__)

# auth_codes = {}


# def send_email_utf8(to_email, name, auth_code):
#     print(" SMTPUTF8 + BYTES 진짜 최종 버전")

#     smtp_user = os.getenv("SMTP_USER")
#     smtp_password = os.getenv("SMTP_PASSWORD")

#     body = f"""안녕하세요 {name}님,

# TripMocha 비밀번호 재설정 인증번호는

# 인증번호: {auth_code}

# 입니다.
# 3분 안에 입력해주세요.
# """

#     msg = EmailMessage(policy=SMTPUTF8)
#     msg.set_content(body, charset="utf-8")

#     msg["Subject"] = "TripMocha Verification Code"
#     msg["From"] = smtp_user
#     msg["To"] = to_email

#     with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
#         server.login(smtp_user, smtp_password)
#         server.sendmail(
#             smtp_user,
#             [to_email],
#             msg.as_bytes(policy=SMTPUTF8)
#         )


# def send_simple_email(to_email, body):
#     smtp_server = "smtp.gmail.com"
#     smtp_port = 587

#     smtp_user = "ayj0519@gmail.com"
#     smtp_password = "앱비밀번호"

#     msg = MIMEText(body, "plain", "utf-8")
#     msg["Subject"] = "TripMocha 아이디 찾기 안내"
#     msg["From"] = smtp_user
#     msg["To"] = to_email

#     server = smtplib.SMTP(smtp_server, smtp_port)
#     server.starttls()
#     server.login(smtp_user, smtp_password)
#     server.sendmail(smtp_user, [to_email], msg.as_string())
#     server.quit()


@api_bp.route("/api/send_auth_code", methods=["POST"])
def send_auth_code():
    email = request.form.get("email")
    user_id = request.form.get("user_id")
    name = request.form.get("name")

    print("받은 데이터:", email, user_id, name)

    if not email:
        return jsonify({"success": False, "message": "이메일이 필요합니다."}), 400

    auth_code = str(random.randint(100000, 999999))

    try:
        # ✅ DB 저장
        db = get_db()
        cursor = db.cursor()

        # (선택) 기존 인증번호 삭제
        cursor.execute(
            "DELETE FROM auth_codes WHERE email = %s",
            (email,)
        )

        cursor.execute(
            """
            INSERT INTO auth_codes (email, auth_code, created_at)
            VALUES (%s, %s, NOW())
            """,
            (email, auth_code)
        )

        db.commit()  

        # ✅ 메일 발송
        msg = Message(
            subject="TripMocha 비밀번호 재설정 인증번호",
            recipients=[email],
            body=f"""안녕하세요 {name}님,

TripMocha 비밀번호 재설정 인증번호는

인증번호: {auth_code}

입니다.
3분 안에 입력해주세요.
""",
        )

        mail.send(msg)

        print("이메일 전송 + DB 저장 성공:", email, auth_code)
        return jsonify({"success": True})

    except Exception as e:
        print("인증번호 처리 오류:", e)
        return jsonify({"success": False, "message": "인증번호 처리 실패"}), 500


@api_bp.route("/api/verify_auth_code", methods=["POST"])
def verify_auth_code():
    email = request.form.get("email")
    user_input_code = request.form.get("auth_code")

    if not email or not user_input_code:
        return jsonify({
            "success": False,
            "message": "요청 데이터가 부족합니다."
        })

    try:
        db = get_db()
        cursor = db.cursor()

        cursor.execute(
            """
            SELECT auth_code, created_at
            FROM auth_codes
            WHERE email = %s
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (email,)
        )

        row = cursor.fetchone()

        if not row:
            return jsonify({
                "success": False,
                "message": "인증번호가 없습니다. 다시 요청해주세요."
            })

        real_code, created_at = row

        # ⏱ 3분 만료 체크
        if datetime.now() - created_at > timedelta(minutes=3):
            return jsonify({
                "success": False,
                "message": "인증번호가 만료되었습니다. 다시 요청해주세요."
            })

        if user_input_code == real_code:
            return jsonify({
                "success": True,
                "message": "인증 성공!"
            })
        else:
            return jsonify({
                "success": False,
                "message": "인증번호가 일치하지 않습니다."
            })

    except Exception as e:
        print("인증번호 검증 오류:", e)
        return jsonify({
            "success": False,
            "message": "서버 오류가 발생했습니다."
        }), 500

@api_bp.route("/api/check_current_password", methods=["POST"])
def check_current_password():
    user_id = session.get("user_id")
    current_pw = request.form.get("current_password")

    if not user_id or not current_pw:
        return jsonify({"success": False})

    db = get_db()
    cursor = db.cursor()

    cursor.execute("SELECT password FROM users WHERE user_id=%s", (user_id,))
    row = cursor.fetchone()

    if not row:
        return jsonify({"success": False})

    stored_pw = row[0]

    if bcrypt.checkpw(current_pw.encode(), stored_pw.encode()):
        return jsonify({"success": True})
    else:
        return jsonify({"success": False})


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
@login_bp.route("/")
def home():
    return render_template("login/login.html")


@login_bp.route("/login")
def login_page():
    return render_template("login/login.html")


@login_bp.route("/join")
def join_page():
    return render_template("login/join.html")


@login_bp.route("/find_id")
def find_id_page():
    return render_template("login/find_id.html")


@login_bp.route("/find_password")
def find_password():
    return render_template("login/find_password.html")


# === index.html 메인 페이지 (LOGIN 후 이동) ===
@login_bp.route("/index")
def index_page():
    return render_template("index.html")


# ----------------------------------------------------
# B. 폼 데이터 처리 라우팅 (POST)
# ----------------------------------------------------


# 7. 로그인 폼 처리 라우트: /login (POST 요청)
@login_bp.route("/login", methods=["POST"])
def process_login():
    user_id = request.form.get("user_id")
    password = request.form.get("password")

    try:
        db_conn = get_db()
        cursor = db_conn.cursor()

        # 아이디 조회 (로그인 제한 컬럼 포함)
        cursor.execute(
            """
            SELECT password, name, login_fail_count, login_locked_until
            FROM users
            WHERE user_id = %s
            """,
            (user_id,),
        )
        row = cursor.fetchone()

        # 아이디 없음
        if not row:
            return render_template(
            "login/login.html",
            error="아이디 또는 비밀번호가 올바르지 않습니다."
        )

        stored_hashed_pw = row[0]
        user_name = row[1]
        login_fail_count = row[2] or 0
        login_locked_until = row[3]

        now = datetime.now()

        # 아이디 잠금 여부 확인
        if login_locked_until and login_locked_until > now:
            return """
                <script>
                    alert("로그인 시도 횟수 초과!\\n10분 후 다시 시도해주세요 😴");
                    history.back();
                </script>
            """

        # 비밀번호 확인
        if bcrypt.checkpw(password.encode("utf-8"), stored_hashed_pw.encode("utf-8")):
            # 로그인 성공 → 실패 기록 초기화
            cursor.execute(
                """
                UPDATE users
                SET login_fail_count = 0,
                    login_locked_until = NULL
                WHERE user_id = %s
                """,
                (user_id,),
            )
            db_conn.commit()

            session["user_id"] = user_id
            session["user_name"] = user_name

            return redirect(url_for("login_bp.index_page"))

        # 비밀번호 틀림 → 실패 횟수 증가
        login_fail_count += 1

        # 5회 실패 → 10분 잠금
        if login_fail_count >= 5:
            lock_until = now + timedelta(minutes=10)
            cursor.execute(
                """
                UPDATE users
                SET login_fail_count = 0,
                    login_locked_until = %s
                WHERE user_id = %s
                """,
                (lock_until, user_id),
            )
            db_conn.commit()

            return """
                <script>
                    alert("로그인 실패 5회 초과!\\n10분 후 다시 시도해주세요 ⛔");
                    history.back();
                </script>
            """

        # 아직 기회 남음
        cursor.execute(
            """
            UPDATE users
            SET login_fail_count = %s
            WHERE user_id = %s
            """,
            (login_fail_count, user_id),
        )
        db_conn.commit()

        remaining = 5 - login_fail_count

        return f"""
            <script>
                alert("아이디 또는 비밀번호가 올바르지 않습니다.\\n남은 시도 횟수: {remaining}회");
                history.back();
            </script>
        """

    except Exception as e:
        print("로그인 오류:", e)
        return """
            <script>
                alert("서버 오류가 발생했습니다.");
                history.back();
            </script>
        """

# 8. 회원가입 폼 처리 라우트: /signup (POST 요청)
@login_bp.route("/signup", methods=["POST"])
def process_signup():
    user_id = request.form.get("user_id")
    password = request.form.get("password")
    name = request.form.get("name")
    birthday = request.form.get("birthday")
    email = request.form.get("email")
    phone = request.form.get("phone")
    gender = request.form.get("gender")
    nation = request.form.get("nation")
    postcode = request.form.get("postcode")
    address = request.form.get("address")
    detail_address = request.form.get("detail_address")
    travel_style = request.form.get("travel_style")

    try:
        # 비밀번호 암호화
        hashed_pw = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode(
            "utf-8"
        )

        db_conn = get_db()
        cursor = db_conn.cursor()

        cursor.execute(
            """
            INSERT INTO users
            (user_id, password, name, birthday, email, phone, gender, nation,
             postcode, address, detail_address, travel_style)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
            (
                user_id,
                hashed_pw,
                name,
                birthday,
                email,
                phone,
                gender,
                nation,
                postcode,
                address,
                detail_address,
                travel_style,
            ),
        )

        db_conn.commit()
        print(" 회원가입 & 비밀번호 암호화 저장 완료")

        # 회원가입 후 자동 로그인
        session["user_id"] = user_id
        session["user_name"] = name

        return redirect(url_for("login_bp.index_page"))

    except Exception as e:
        print("===== 회원가입 오류 발생! =====")
        traceback.print_exc()  # 전체 에러 로그 출력
        print("===== 오류 끝 =====")

        return """
            <script>
                alert("회원가입 중 오류가 발생했습니다.");
                history.back();
            </script>
        """


@login_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


@login_bp.route("/profile")
def profile_page():
    if "user_id" not in session:
        return redirect(url_for("login_bp.login_page"))

    try:
        db = get_db()
        cursor = db.cursor()

        cursor.execute(
            """
            SELECT user_id, name, birthday, email, phone, gender, nation, 
                   postcode, address, detail_address, travel_style
            FROM users
            WHERE user_id = %s
        """,
            (session["user_id"],),
        )

        user = cursor.fetchone()

        return render_template("login/profile.html", user=user)

    except Exception as e:
        print("프로필 조회 오류:", e)
        return "<script>alert('서버 오류 발생'); history.back();</script>"


# ----------------------------------------------------
# B-1. 아이디 중복 확인 라우팅 (AJAX용)
# ----------------------------------------------------
# NOTE: 이 함수를 routes/models.py나 별도의 services/auth.py로 분리하는 것이 좋습니다.


def check_id_exists_in_db(user_id):
    """
    Placeholder 함수: 실제 데이터베이스에서 해당 user_id가 존재하는지 확인하는 함수
    """
    # 예시: 'admin', 'testuser' 아이디는 이미 존재한다고 가정
    return user_id in ["admin", "testuser"]


@api_bp.route("/api/check_userid", methods=["POST"])
def check_userid():
    user_id = request.form.get("user_id")

    if not user_id:
        return jsonify({"exists": True})

    try:
        db_conn = get_db()
        cursor = db_conn.cursor()

        cursor.execute("SELECT user_id FROM users WHERE user_id = %s", (user_id,))
        row = cursor.fetchone()

        if row:
            return jsonify({"exists": True})  # 이미 존재
        else:
            return jsonify({"exists": False})  # 사용 가능

    except Exception as e:
        print("아이디 중복확인 오류:", e)
        return jsonify({"exists": True})  # 오류 시 안전하게 '중복' 처리


@login_bp.route("/find_id_process", methods=["POST"])
def find_id_process():
    name = request.form.get("name")
    birthday = request.form.get("birthday")
    email = request.form.get("email")

    try:
        db = get_db()
        cursor = db.cursor()

        cursor.execute(
            """
            SELECT user_id
            FROM users
            WHERE name = %s AND birthday = %s AND email = %s
        """,
            (name, birthday, email),
        )

        results = cursor.fetchall()

        if not results:
            return render_template(
                "login/find_id.html",
                toast="일치하는 정보를 찾을 수 없습니다."
            )

        #  아이디 마스킹 후 화면 표시
        masked_ids = [mask_user_id(row[0]) for row in results]
        id_text = "\\n".join(masked_ids)

        return render_template(
            "login/find_id.html",
            toast=f"고객님의 아이디는 다음과 같습니다:\n{id_text}"
        )

    except Exception as e:
        print("아이디 찾기 오류:", e)
        return """
            <script>
                alert("서버 오류가 발생했습니다.");
                history.back();
            </script>
        """


@login_bp.route("/reset_password", methods=["POST"])
def reset_password():
    user_id = request.form.get("user_id")
    new_password = request.form.get("new_password")

    try:
        hashed_pw = bcrypt.hashpw(
            new_password.encode("utf-8"), bcrypt.gensalt()
        ).decode("utf-8")

        db = get_db()
        cursor = db.cursor()

        # 1️⃣ 비밀번호 변경
        cursor.execute(
            """
            UPDATE users
            SET password = %s
            WHERE user_id = %s
            """,
            (hashed_pw, user_id),
        )

        # 2️⃣ 🔥 비밀번호 변경 로그 기록 (핵심)
        cursor.execute(
            """
            INSERT INTO password_reset_log
            (user_id, reset_time, ip_address, success)
            VALUES (%s, NOW(), %s, 1)
            """,
            (user_id, request.remote_addr),
        )

        db.commit()

        session.clear()  # ✅ 맨 마지막에
        return jsonify({"success": True})

    except Exception as e:
        print("비밀번호 변경 오류:", e)

        # 실패 로그도 남기고 싶다면 (선택)
        try:
            db = get_db()
            cursor = db.cursor()
            cursor.execute(
                """
                INSERT INTO password_reset_log
                (user_id, reset_time, ip_address, success)
                VALUES (%s, NOW(), %s, 0)
                """,
                (user_id, request.remote_addr),
            )
            db.commit()
        except:
            pass

        return jsonify({"success": False, "message": "비밀번호 변경 실패"}), 500


@login_bp.route("/profile/update", methods=["POST"])
def update_profile():
    user_id = session.get("user_id")

    if not user_id:
        return "<script>alert('로그인이 필요합니다'); location.href='/login';</script>"

    current_pw = request.form.get("current_password")
    if not current_pw:
        return "<script>alert('현재 비밀번호를 입력해주세요'); history.back();</script>"

    name = request.form.get("name")
    birthday = request.form.get("birthday")
    email = request.form.get("email")
    phone = request.form.get("phone")
    gender = request.form.get("gender")
    nation = request.form.get("nation")
    postcode = request.form.get("postcode")
    address = request.form.get("address")
    detail_address = request.form.get("detail_address")
    travel_style = request.form.get("travel_style")

    new_pw = request.form.get("new_password")
    new_pw_confirm = request.form.get("new_password_confirm")

    db = get_db()
    cursor = db.cursor()

    # ⭐ 어떤 수정이든 무조건 현재 비밀번호 먼저 검증
    cursor.execute("SELECT password FROM users WHERE user_id=%s", (user_id,))
    row = cursor.fetchone()

    if not row:
        return "<script>alert('사용자 정보를 찾을 수 없습니다'); history.back();</script>"

    stored_pw = row[0]

    if not bcrypt.checkpw(current_pw.encode(), stored_pw.encode()):
        return "<script>alert('현재 비밀번호가 일치하지 않습니다'); history.back();</script>"

    # ⭐ 비밀번호 변경 (선택)
    if new_pw:
        if new_pw != new_pw_confirm:
            return "<script>alert('새 비밀번호가 일치하지 않습니다'); history.back();</script>"

        hashed_pw = bcrypt.hashpw(new_pw.encode(), bcrypt.gensalt()).decode("utf-8")

        cursor.execute(
            """
            UPDATE users
            SET password=%s
            WHERE user_id=%s
            """,
            (hashed_pw, user_id),
        )

    # ⭐ 일반 정보 업데이트
    cursor.execute(
        """
        UPDATE users
        SET name=%s, birthday=%s, email=%s, phone=%s,
            gender=%s, nation=%s, postcode=%s, address=%s,
            detail_address=%s, travel_style=%s
        WHERE user_id=%s
        """,
        (
            name,
            birthday,
            email,
            phone,
            gender,
            nation,
            postcode,
            address,
            detail_address,
            travel_style,
            user_id,
        ),
    )

    db.commit()
    session["user_name"] = name

    return redirect(url_for("index"))



