/* ================================
    기본 입력 유틸리티
================================ */

// 전화번호 자동 하이픈
function autoHyphenate(input) {
    let number = input.value.replace(/[^0-9]/g, "");
    if (number.length < 4) input.value = number;
    else if (number.length < 8) input.value = number.substr(0, 3) + "-" + number.substr(3);
    else input.value = number.substr(0, 3) + "-" + number.substr(3, 4) + "-" + number.substr(7, 4);
}

// 영어 + 숫자만 허용
function filterEnglishOnly(input) {
    input.value = input.value.replace(/[^a-zA-Z0-9]/g, '');
}

// 숫자만 허용
function filterNumberOnly(input) {
    input.value = input.value.replace(/[^0-9]/g, '');
}


/* ================================
    모달 알림
================================ */
function alertModal(message) {
    let modal = document.getElementById('custom-modal');

    if (!modal) {
        modal = document.createElement('div');
        modal.id = 'custom-modal';
        modal.className =
            'fixed inset-0 bg-black bg-opacity-40 flex items-center justify-center z-50 opacity-0 pointer-events-none transition-opacity';

        modal.innerHTML = `
            <div class="bg-white p-6 rounded-lg shadow-xl w-80 transform scale-95 transition-transform">
                <p id="modal-message" class="text-gray-800 text-lg mb-4 whitespace-pre-wrap"></p>
                <button id="modal-ok-btn" class="w-full py-2 bg-green-600 text-white rounded-lg hover:bg-green-700">
                    확인
                </button>
            </div>
        `;

        document.body.appendChild(modal);

        document.getElementById('modal-ok-btn').onclick = () => {
            modal.classList.add('opacity-0', 'pointer-events-none');
        };
    }

    document.getElementById('modal-message').textContent = message;
    modal.classList.remove('opacity-0', 'pointer-events-none');
}


/* ================================
    성별/국적 버튼 선택
================================ */
function toggleSelection($container, hiddenInputId) {
    $container.on("click", ".select-btn", function () {
        $container.find(".select-btn").removeClass("selected");
        $(this).addClass("selected");

        $("#" + hiddenInputId).val($(this).data("value"));

        updateSubmitButtonState();
    });
}


/* ================================
   아이디 자동 중복 확인
================================ */

let idCheckTimer = null;
let isIdChecked = false;
let isIdAvailable = false;

function setupIdCheck() {

    $("#user_id").on("input", function () {
        const userId = $(this).val().trim();
        const $msg = $("#id_check_message");
        const $btn = $("#check_duplicate_btn");

        // 입력 즉시 버튼 비활성화(굳이 안 써도 되지만 안전용)
        $btn.prop("disabled", true);

        // 영어+숫자만 허용
        filterEnglishOnly(this);

        // 메시지 초기화
        $msg.text("").removeClass("text-red-500 text-green-600");

        // 이전 타이머 제거
        clearTimeout(idCheckTimer);

        if (userId.length < 3) {
            $msg.text("아이디는 최소 3글자 이상입니다.")
                .addClass("text-red-500");
            isIdAvailable = false;
            isIdChecked = false;
            updateSubmitButtonState();
            return;
        }

        // 0.5초 뒤 자동 검사 (Debounce)
        idCheckTimer = setTimeout(() => {

            $.ajax({
                url: "/api/check_userid",
                method: "POST",
                data: { user_id: userId },

                success: function (res) {
                    isIdChecked = true;

                    if (res.exists) {
                        // ❌ 중복
                        isIdAvailable = false;

                        $msg.text("이미 사용 중인 아이디입니다.")
                            .removeClass("text-green-600")
                            .addClass("text-red-500");

                    } else {
                        // ⭕ 사용 가능
                        isIdAvailable = true;

                        $msg.text("사용 가능한 아이디입니다!")
                            .removeClass("text-red-500")
                            .addClass("text-green-600");

                    }

                    updateSubmitButtonState();
                },

                error: function () {
                    $msg.text("서버 오류가 발생했습니다.")
                        .removeClass("text-green-600")
                        .addClass("text-red-500");
                }
            });

        }, 500); // 입력 후 0.5초 지나면 자동 검사
    });
}


/* ================================
    비밀번호 일치 검사
================================ */
function setupPasswordCheck() {
    $('#password, #password_confirm').on('input', function () {
        const pw = $('#password').val();
        const cf = $('#password_confirm').val();
        const $msg = $('#password_match_message');

        if (!pw || !cf) {
            $msg.addClass("hidden");
            return;
        }

        if (pw === cf) {
            $msg.text("비밀번호가 일치합니다.")
                .removeClass().addClass("text-green-600");
        } else {
            $msg.text("비밀번호가 일치하지 않습니다.")
                .removeClass().addClass("text-red-500");
        }

        updateSubmitButtonState();
    });
}

function checkPasswordStrength(pw) {
    let strength = 0;

    if (pw.length >= 8) strength++;               // 길이 체크
    if (/[A-Z]/.test(pw)) strength++;             // 대문자
    if (/[0-9]/.test(pw)) strength++;             // 숫자
    if (/[^A-Za-z0-9]/.test(pw)) strength++;      // 특수문자

    return strength;
}




/* ================================
    이용약관 체크 기능 추가 (중요)
================================ */

// 필수 약관이 모두 체크되었는지 확인
function isRequiredTermsChecked() {
    return $('.required-term').toArray().every(c => $(c).is(':checked'));
}

function setupTerms() {

    // ⭐ 전체 선택 눌렀을 때 모든 체크박스 ON/OFF
    $('#term_all').on('change', function () {
        const checked = $(this).is(':checked');
        $('.term-check').prop('checked', checked);
        updateSubmitButtonState();
    });

    // ⭐ 개별 체크박스 변경 → 전체 선택 체크 여부 자동 업데이트
    $('.term-check').on('change', function () {
        const total = $('.term-check').length;
        const checked = $('.term-check:checked').length;

        // 전부 선택되면 전체 선택도 체크 / 아니면 해제
        $('#term_all').prop('checked', total === checked);

        updateSubmitButtonState();
    });
}



/* ================================
    가입 버튼 활성/비활성
================================ */
function updateSubmitButtonState() {
    const requiredFilled = $(".signup-form [required]").toArray()
        .every(e => $(e).val().trim() !== "");

    const pwMatch = $('#password').val() === $('#password_confirm').val();
    const termsOk = isRequiredTermsChecked(); // ← 약관 확인 추가됨

    const canSubmit = requiredFilled && isIdAvailable && pwMatch && termsOk;

    const $btn = $('#submit_btn');

    if (canSubmit) {
        $btn.prop("disabled", false)
            .removeClass("bg-indigo-400")
            .addClass("bg-indigo-600");
    } else {
        $btn.prop("disabled", true)
            .removeClass("bg-indigo-600")
            .addClass("bg-indigo-400");
    }
}


/* ================================
    여행 스타일 선택 (최대 4개)
================================ */
function setupTravelStyleSelection() {
    const max = 4;
    const selected = new Set();

    $(".style-btn").on("click", function () {
        const v = $(this).data("value");

        if ($(this).hasClass("selected")) {
            $(this).removeClass("selected");
            selected.delete(v);
        } else {
            if (selected.size >= max) {
                showToast("여행 스타일은 최대 4개까지 선택할 수 있어요!");
                return;
            }
            $(this).addClass("selected");
            selected.add(v);
        }

        $("#travel_style").val([...selected].join(","));
    });
}


/* ================================
    주소 검색 (카카오)
================================ */
function setupAddressSearch() {
    $("#search_address_btn").on("click", function () {
        new daum.Postcode({
            oncomplete: function (data) {
                $("#postcode").val(data.zonecode);
                $("#address").val(data.roadAddress || data.jibunAddress);
                $("#detail_address").focus();
            }
        }).open();
    });
}


/* ================================
    폼 제출 처리
================================ */
function setupFormSubmit() {
    $(".signup-form").on("submit", function (e) {

        if (!isIdChecked || !isIdAvailable) {
            e.preventDefault();
            alertModal("아이디 중복 확인을 먼저 진행해주세요!");
            return;
        }

        if ($("#password").val() !== $("#password_confirm").val()) {
            e.preventDefault();
            alertModal("비밀번호가 일치하지 않습니다.");
            return;
        }

        if (!isRequiredTermsChecked()) {
            e.preventDefault();
            alertModal("필수 약관에 모두 동의해야 회원가입이 가능합니다!");
            return;
        }

    });
}

/* ================================
    비밀번호 강도 표시 기능
================================ */

$("#password").on("input", function () {
    const pw = $(this).val();
    const $strengthMsg = $("#password_strength");

    $strengthMsg.removeClass("pw-weak pw-medium pw-strong");

    if (!pw) {
        $strengthMsg.text("");
        return;
    }

    const strength = checkPasswordStrength(pw);

    if (strength <= 1) {
        $strengthMsg.text("비밀번호 강도: 약함").addClass("pw-weak");
    } else if (strength <= 3) {
        $strengthMsg.text("비밀번호 강도: 보통").addClass("pw-medium");
    } else {
        $strengthMsg.text("비밀번호 강도: 강함").addClass("pw-strong");
    }
});

/* ================================
    실행 구간
================================ */
$(document).ready(() => {

    $("#phone_number").on('input', function () {
        autoHyphenate(this);
        updateSubmitButtonState();
    });

    $("#birthday").on("input", function () {
        filterNumberOnly(this);
        updateSubmitButtonState();
    });

    toggleSelection($("#gender-buttons"), "selected-gender");
    toggleSelection($("#nation-buttons"), "selected-nation");

    setupIdCheck();
    setupPasswordCheck();
    setupTerms();  // ← 이용약관 기능
    setupTravelStyleSelection();
    setupAddressSearch();
    setupFormSubmit();
});


function showToast(message) {
    const $toast = $("#toast");

    $toast.text(message).removeClass("hidden");

    setTimeout(() => {
        $toast.addClass("show");
    }, 10);

    setTimeout(() => {
        $toast.removeClass("show");

        setTimeout(() => {
            $toast.addClass("hidden");
        }, 300);
    }, 2000);
}

