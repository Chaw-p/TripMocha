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
    아이디 중복 확인
================================ */

let isIdChecked = false;
let isIdAvailable = false;

function setupIdCheck() {

    // 아이디 입력 중이면 상태 초기화
    $('#user_id').on('input', function () {
        filterEnglishOnly(this);
        isIdChecked = false;
        isIdAvailable = false;

        $('#id_check_message')
            .text("아이디는 영문+숫자만 입력하세요.")
            .removeClass()
            .addClass("text-gray-500");

        updateSubmitButtonState();
    });


    // 중복확인 버튼 클릭
    $('#check_duplicate_btn').on('click', function () {
        const userId = $('#user_id').val().trim();
        const $message = $('#id_check_message');
        const $btn = $(this);

        if (userId.length < 3) {
            $message.text("아이디는 최소 3글자 이상입니다.")
                .removeClass().addClass("text-red-500");
            return;
        }

        $btn.prop("disabled", true).text("확인 중...");

        $.ajax({
            url: "/api/check_userid",
            method: "POST",
            data: { user_id: userId },

            success: function (res) {
                $btn.prop("disabled", false).text("중복 확인");

                isIdChecked = true;

                if (res.exists) {
                    // 이미 있는 아이디
                    isIdAvailable = false;
                    $message.text("이미 사용 중인 아이디입니다.").removeClass().addClass("text-red-500");
                } else {
                    // 사용 가능
                    isIdAvailable = true;
                    $message.text("사용 가능한 아이디입니다!").removeClass().addClass("text-green-600");
                }

                updateSubmitButtonState();
            },

            error: function () {
                alertModal("서버 오류가 발생했습니다!");
                $btn.prop("disabled", false).text("중복 확인");
            }
        });

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


/* ================================
    가입 버튼 활성/비활성 관리
================================ */
function updateSubmitButtonState() {
    const requiredFilled = $(".signup-form [required]").toArray()
        .every(e => $(e).val().trim() !== "");

    const pwMatch = $('#password').val() === $('#password_confirm').val();

    const canSubmit = requiredFilled && isIdAvailable && pwMatch;

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
                alertModal("여행 스타일은 최대 4개까지 선택할 수 있어요!");
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

        // 정상 제출 → 서버에서 회원가입 처리
    });
}


/* ================================
    실행 구간
================================ */
$(document).ready(() => {

    // 입력 이벤트 처리
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
    setupTravelStyleSelection();
    setupAddressSearch();
    setupFormSubmit();

});
