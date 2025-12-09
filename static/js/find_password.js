const $newPasswordGroup = $("#newPasswordGroup");
function filterNumberOnly(input) {
    input.value = input.value.replace(/[^0-9]/g, '');
}

// =======================================================
// B. 인증 상태 변수 및 타이머 및 UI 관리
// =======================================================
let authTimer = null;
let authTimeLeft = 0; // 초 단위

//  [추가] 메시지 영역 DOM 요소 캐시 (alert 대신 사용)
const $messageArea = $('#message_area');

/**
 * 메시지 표시 함수 (alert 대신 사용)
 */
function showMessage(message, type = 'success') {
    // $messageArea가 jQuery 객체인지 확인하고 클래스를 초기화합니다.
    if ($messageArea.length === 0) return; 
    
    $messageArea.removeClass().addClass('p-3 rounded-lg text-sm mb-4')
    $messageArea.show(); 

    if (type === 'success') {
        $messageArea.addClass('bg-green-100 text-green-700').html(`✅ ${message}`);
    } else if (type === 'error') {
        $messageArea.addClass('bg-red-100 text-red-700').html(`❌ ${message}`);
    } else { // default for info
        $messageArea.addClass('bg-blue-100 text-blue-700').html(`ℹ️ ${message}`);
    }
}

/**
 * 버튼에 로딩 스피너를 표시합니다.
 */
function showButtonLoading($btn, text) {
    $btn.data('original-text', $btn.text());
    $btn.html(`<svg class="animate-spin h-5 w-5 mr-3 inline text-white" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg> ${text}`).prop('disabled', true).addClass('opacity-50 cursor-not-allowed');
}

/**
 * 버튼의 로딩 스피너를 제거하고 원래 텍스트로 복구합니다.
 */
function hideButtonLoading($btn, reEnable = true) {
    const originalText = $btn.data('original-text');
    
    if (originalText && typeof originalText === 'string') {
        $btn.html(originalText);
    } else {
        $btn.html($btn.html().replace(/<svg.*?>.*?<\/svg>/s, '')); 
    }
    
    if (reEnable) {
        $btn.prop('disabled', false).removeClass('opacity-50 cursor-not-allowed');
    }
}


/**
 * 인증번호 타이머를 시작하고 화면에 남은 시간을 표시합니다.
 */
function startAuthTimer(duration) {
    authTimeLeft = duration;
    clearInterval(authTimer);

    const $authBtn = $('#send_auth_btn');
    const $authCodeInput = $('#auth_code');
    const $submitBtn = $('#submit_btn');

    $authBtn.prop('disabled', true).addClass('opacity-50 cursor-not-allowed');

    authTimer = setInterval(() => {
        const minutes = Math.floor(authTimeLeft / 60);
        const seconds = authTimeLeft % 60;
        
        $authBtn.text(`재전송 (${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')})`);

        if (authTimeLeft <= 0) {
            clearInterval(authTimer);
            $authBtn.prop('disabled', false).text('인증번호 재전송').removeClass('opacity-50 cursor-not-allowed');
            $authCodeInput.prop('disabled', true);
            $submitBtn.prop('disabled', true).addClass('bg-gray-400');
            showMessage('인증 시간이 만료되었습니다. 인증번호를 다시 요청해주세요.', 'error'); // 📢 alert 대신 showMessage 사용
        }

        authTimeLeft--;
    }, 1000);
}


// =======================================================
// C. DOM 로드 및 이벤트 리스너 설정
// =======================================================
$(document).ready(function() {
    const $form = $('#find-password-form'); //  [추가] 폼 ID 가정
    const $userId = $('input[name="user_id"]');
    const $name = $('input[name="name"]');
    const $email = $('#email');
    const $authBtn = $('#send_auth_btn');
    const $authCodeInput = $('#auth_code');
    const $submitBtn = $('#reset_btn');
    const $newPasswordInput = $('#new_password'); //  [추가] 새 비밀번호 입력 필드 ID 가정

    // 초기 상태: 인증번호 입력 필드와 제출 버튼 비활성화
    $authCodeInput.prop('disabled', true);
    $submitBtn.prop('disabled', true).addClass('bg-gray-400');
    $newPasswordInput.prop('disabled', true); //  [추가] 새 비밀번호 필드 초기 비활성화
    $messageArea.hide();

    
    // 2. 인증번호 입력 필드에 숫자 필터링 및 6자리 검증
    $authCodeInput.on('input', function() {
        filterNumberOnly(this); // 숫자만 입력되도록 필터링
        
        const code = $(this).val();
        
        // 6자리 입력 시 바로 검증 요청
        if (code.length === 6) {
             showButtonLoading($submitBtn, '확인 중...'); //  [수정] 로딩 표시
             $submitBtn.prop('disabled', true); // 중복 클릭 방지
             
             // 서버에 인증번호 검증 요청 (AJAX)
             $.post('/api/verify_auth_code', {
                 email: $email.val(),
                 auth_code: code
             }, function(response) {
                 
                 //  [추가] 서버 응답 유효성 검사
                 if (!response || response === null) {
                     showMessage('서버 응답이 없습니다. 관리자에게 문의하세요.', 'error');
                     hideButtonLoading($submitBtn, true);
                     return;
                 }
                 
                 if (response.success) {
                    showMessage('인증이 완료되었습니다. 새로운 비밀번호를 설정해주세요.', 'success');
                    clearInterval(authTimer); // 타이머 중지
                    $authCodeInput.prop('disabled', true).val('인증 완료');
                    $authBtn.prop('disabled', true).text('인증 완료').css('background-color', '#38a169');
                    
                    $newPasswordGroup.css('display', 'block');
                    $newPasswordInput.prop('disabled', false); 
                    
                    setTimeout(() => {
                        $newPasswordInput.focus();
                    }, 50); // 50ms 지연
                    
                    hideButtonLoading($submitBtn, false); // 로딩 제거, 버튼은 활성화 상태
                    $submitBtn.prop('disabled', false); 
                    
                    $form.data('verified', true); 
                } else {
                    showMessage(response.message || '인증번호가 일치하지 않습니다.', 'error'); 
                    hideButtonLoading($submitBtn, true);
                    $authCodeInput.prop('disabled', false); // 재입력 가능하도록
                    $submitBtn.prop('disabled', true);
                }
            });
        } else {
            // 6자리가 아니면 제출 버튼 비활성화
            $submitBtn.prop('disabled', true).addClass('bg-gray-400');
        }
    });

    // 3. 인증번호 받기 버튼 클릭 이벤트 (AJAX 호출 로직)
    $authBtn.on('click', function() {
        $messageArea.hide();
        // 필수 필드 유효성 검사
        if ($userId.val().length < 1 || $name.val().length < 1 || $email.val().length < 5) {
            showMessage('아이디, 이름, 이메일을 정확히 입력해주세요.', 'error');
            return;
        }   

        showButtonLoading($authBtn, '발송 중...'); 
        
        // 서버에 인증번호 발송 요청 (AJAX)
        $.post('/api/send_auth_code', {
            user_id: $userId.val(),
            name: $name.val(),
            email: $email.val()
        }, function(response) {
            
            //  [추가] 서버 응답 유효성 검사
            if (!response || response === null) {
                showMessage('서버 응답이 없습니다. 관리자에게 문의하세요.', 'error');
                hideButtonLoading($authBtn, true);
                return;
            }
            
            if (response.success) {
                showMessage('인증번호가 이메일로 발송되었습니다. 3분 안에 입력해주세요.', 'success');
                
                // 인증번호 입력 필드 활성화 및 포커스
                $authCodeInput.val('').prop('disabled', false).focus();
                
                // 인증 타이머 시작 (3분 = 180초)
                startAuthTimer(180);

            } else {
                showMessage(response.message || '인증번호 발송에 실패했습니다. 사용자 정보를 확인해주세요.', 'error'); // 📢 alert 대신 showMessage 사용
            }
            
            // 발송 실패 시에만 버튼 복구 (성공 시 타이머가 복구함)
            if (!response.success) {
                hideButtonLoading($authBtn, true);
            }
            
        }).fail(function() {
            showMessage('서버와 통신할 수 없습니다. 백엔드 서버가 실행 중인지 확인하세요.', 'error'); // 📢 alert 대신 showMessage 사용
            hideButtonLoading($authBtn, true);
        });
    });

    // 4. 비밀번호 재설정 최종 제출 (폼 제출 이벤트)
    $form.on('submit', function(e) {
        e.preventDefault(); // 기본 폼 제출을 막고 AJAX로 처리

        if (!$form.data('verified')) {
            showMessage("먼저 이메일 인증을 완료해주세요.", 'error');
            return;
        }

        const newPassword = $newPasswordInput.val();
        if (newPassword.length < 8) {
            showMessage("비밀번호는 최소 8자 이상이어야 합니다.", 'error');
            return;
        }
        
        showButtonLoading($submitBtn, '재설정 중...');
        
        // 서버로 보낼 데이터 준비
        const postData = {
            user_id: $userId.val(), 
            name: $name.val(),
            email: $email.val(),    
            new_password: newPassword
        };

        // 서버에 비밀번호 재설정 요청 (AJAX)
        $.post('/reset_password', postData, function(response) { 
            
            //  [추가] response 유효성 검사
            if (!response || response === null) {
                showMessage('서버 응답이 없습니다. 관리자에게 문의하세요. (reset_password)', 'error');
                hideButtonLoading($submitBtn, true);
                return;
            }
            
            if (response.success) {
                showMessage('비밀번호가 성공적으로 재설정되었습니다. 로그인 페이지로 이동합니다.', 'success');
                setTimeout(() => {
                    window.location.href = "/login"; // 명시적 경로로 수정
                }, 2000); // 2초 후 이동 (메시지를 읽을 시간 부여)

            } else {
                showMessage(response.message || '비밀번호 재설정에 실패했습니다. 다시 시도해주세요.', 'error');
                hideButtonLoading($submitBtn, true);
            }

        }).fail(function() {
            showMessage('비밀번호 재설정 서버와 통신할 수 없습니다.', 'error');
            hideButtonLoading($submitBtn, true);
        });
    });
});


$("#reset_btn").on("click", function () {
    let pw = $("#new_password").val();
    let pw2 = $("#new_password_check").val();

    if (pw.length < 8) {
        alert("비밀번호는 8자 이상이어야 합니다.");
        return;
    }
    if (pw !== pw2) {
        alert("비밀번호가 일치하지 않습니다.");
        return;
    }

    $("#find-password-form").submit();  // ← 비밀번호 변경 API 호출
});
