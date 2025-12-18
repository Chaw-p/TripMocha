// =======================================================
// A. 공용 유틸
// =======================================================

function filterNumberOnly(input) {
    input.value = input.value.replace(/[^0-9]/g, '');
}

// 메시지 영역
const $messageArea = $('#message_area');

function showMessage(message, type = 'info') {
    if ($messageArea.length === 0) return;

    $messageArea
        .removeClass()
        .addClass('p-3 rounded-lg text-sm mb-4')
        .show();

    if (type === 'success') {
        $messageArea.addClass('bg-green-100 text-green-700').html(`✅ ${message}`);
    } else if (type === 'error') {
        $messageArea.addClass('bg-red-100 text-red-700').html(`❌ ${message}`);
    } else {
        $messageArea.addClass('bg-blue-100 text-blue-700').html(`ℹ️ ${message}`);
    }
}

// 버튼 로딩
function showButtonLoading($btn, text = "로딩중") {
    $btn.data("original-html", $btn.html());
    $btn.html(`
        <span style="display:inline-flex; align-items:center; gap:6px;">
            <span class="spinner"></span>
            ${text}
        </span>
    `);
    $btn.prop("disabled", true).css({ opacity: 0.7, cursor: "not-allowed" });
}

function hideButtonLoading($btn, enable = true) {
    const original = $btn.data("original-html");
    if (original) $btn.html(original);
    if (enable) {
        $btn.prop("disabled", false).css({ opacity: 1, cursor: "pointer" });
    }
}

// 스피너 스타일
(function injectSpinnerStyle() {
    if (document.getElementById("spinner-style")) return;
    const style = document.createElement("style");
    style.id = "spinner-style";
    style.innerHTML = `
        .spinner {
            width: 14px;
            height: 14px;
            border: 2px solid rgba(255,255,255,0.3);
            border-top: 2px solid white;
            border-radius: 50%;
            animation: spin 0.8s linear infinite;
        }
        @keyframes spin { to { transform: rotate(360deg); } }
    `;
    document.head.appendChild(style);
})();


// =======================================================
// B. 인증 타이머
// =======================================================

let authTimer = null;
let authTimeLeft = 0;

function startAuthTimer(seconds) {
    clearInterval(authTimer);
    authTimeLeft = seconds;

    const $authBtn = $('#send_auth_btn');
    const $authCode = $('#auth_code');

    $authBtn.prop('disabled', true);

    authTimer = setInterval(() => {
        const m = Math.floor(authTimeLeft / 60);
        const s = authTimeLeft % 60;

        $authBtn.text(`재전송 (${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')})`);

        if (authTimeLeft <= 0) {
            clearInterval(authTimer);
            $authBtn
            .text('인증번호 재전송')
            .prop('disabled', false)
            .css({
                cursor: 'pointer',
                opacity: 1
            });
            $authBtn.addClass('resend-active');
            $authCode.prop('disabled', true);
            showMessage('인증 시간이 만료되었습니다.', 'error');
        }

        authTimeLeft--;
    }, 1000);
}


// =======================================================
// C. DOM Ready
// =======================================================

$(document).ready(function () {

    const $form = $('#find-password-form');
    const $userId = $('input[name="user_id"]');
    const $name = $('input[name="name"]');
    const $email = $('#email');

    const $authBtn = $('#send_auth_btn');
    const $authCode = $('#auth_code');

    const $newPasswordGroup = $('#newPasswordGroup');
    const $newPassword = $('#new_password');
    const $newPasswordCheck = $('#new_password_check');
    const $resetBtn = $('#reset_btn');

    // 초기 상태
    $('#authCodeGroup').hide();     // ⬅️ 아예 안 보이게
    $authCode.prop('disabled', true);
    $newPasswordGroup.hide();
    $messageArea.hide();
    $form.data('verified', false);

    // ---------------------------------------------------
    // 1. 인증번호 발송
    // ---------------------------------------------------
    $authBtn.on('click', function () {

        if (!$userId.val() || !$name.val() || !$email.val()) {
            showMessage('아이디, 이름, 이메일을 입력하세요.', 'error');
            return;
        }
        
        // 이메일 형식 검사
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

        if (!emailRegex.test($email.val())) {
            showMessage('해당 이메일에 대한 아이디가 없습니다.', 'error');
            return;
        }


        showButtonLoading($authBtn, '발송 중...');

        $.post('/api/send_auth_code', {
            user_id: $userId.val(),
            name: $name.val(),
            email: $email.val()
        }, function (res) {

            if (res.success) {
            showMessage('인증번호를 이메일로 보냈어요! (3분)', 'success');

            // 🔥 서버 성공 후에만 등장
            if (!$('#authCodeGroup').is(':visible')) {
                $('#authCodeGroup').slideDown(200);
            }

            $authCode.val('').prop('disabled', false).focus();
            startAuthTimer(180);
        } else {
                showMessage(res.message || '인증번호 발송 실패', 'error');
                hideButtonLoading($authBtn);
            }

        }).fail(() => {
            showMessage('서버 통신 실패', 'error');
            hideButtonLoading($authBtn);
        });
    });

    // ---------------------------------------------------
    // 2. 인증번호 입력 (6자리)
    // ---------------------------------------------------
    $authCode.on('input', function () {
        filterNumberOnly(this);
        if (this.value.length !== 6) return;

        $.post('/api/verify_auth_code', {
            email: $email.val(),
            auth_code: this.value
        }, function (res) {

            if (res.success) {
                clearInterval(authTimer);
                showMessage('인증 성공! 비밀번호를 설정하세요.', 'success');

                $authCode.val('인증 완료').prop('disabled', true);
                $authBtn.text('인증 완료').prop('disabled', true);

                $newPasswordGroup.slideDown();
                $form.data('verified', true);
            } else {
                showMessage(res.message || '인증번호가 틀렸어요', 'error');
                $authCode.val('').focus();
            }
        });
    });

    // ---------------------------------------------------
    // 3. 비밀번호 재설정
    // ---------------------------------------------------
    $resetBtn.on('click', function () {

        if (!$form.data('verified')) {
            showMessage('이메일 인증부터 하세요!', 'error');
            return;
        }

        const pw = $newPassword.val();
        const pw2 = $newPasswordCheck.val();

        if (pw.length < 8) {
            showMessage('비밀번호는 8자 이상!', 'error');
            return;
        }
        if (pw !== pw2) {
            showMessage('비밀번호가 서로 안 맞아요', 'error');
            return;
        }

        showButtonLoading($resetBtn, '변경 중...');

        $.post('/reset_password', {
            user_id: $userId.val(),
            name: $name.val(),
            email: $email.val(),
            new_password: pw
        }, function (res) {

            if (res.success) {
                showMessage('비밀번호 변경 완료! 로그인으로 이동합니다.', 'success');
                setTimeout(() => location.href = '/login', 2000);
            } else {
                showMessage(res.message || '비밀번호 변경 실패', 'error');
                hideButtonLoading($resetBtn);
            }
        }).fail(() => {
            showMessage('서버 오류', 'error');
            hideButtonLoading($resetBtn);
        });
    });

});
