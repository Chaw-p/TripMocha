// =======================================================
// A. 유틸리티 함수 (Global Scope)
// =======================================================

/**
 * 휴대전화 번호에 자동 하이픈을 삽입합니다.
 */
function autoHyphenate(input) {
    let number = input.value.replace(/[^0-9]/g, "");
    let temp = "";

    if (number.length < 4) {
        temp += number;
    } else if (number.length < 8) {
        temp += number.substr(0, 3);
        temp += "-";
        temp += number.substr(3);
    } else {
        temp += number.substr(0, 3);
        temp += "-";
        temp += number.substr(3, 4);
        temp += "-";
        temp += number.substr(7, 4);
    }
    input.value = temp;
}

/**
 * 입력값에서 숫자만 허용하고 나머지는 제거합니다. (생년월일용)
 */
function filterNumberOnly(input) {
    let filteredValue = input.value.replace(/[^0-9]/g, '');
    if (input.value !== filteredValue) {
        input.value = filteredValue;
    }
}


// =======================================================
// B. DOM 로드 및 이벤트 리스너 설정
// =======================================================
$(document).ready(function () {

    // 1. 휴대전화 필드 (id="phone_number")에 자동 하이픈 기능 연결
    $('#phone_number').on('input', function () {
        autoHyphenate(this);
    });

    // 2. 생년월일 필드 (id="birthday")에 숫자 필터링 기능 연결
    $('#birthday').on('input', function () {
        filterNumberOnly(this);
    });

});


// =======================================================
// C. Toast 메시지 처리
// =======================================================
// $(document).ready(function () {
//     const message = $("body").data("toast");

//     if (message) {
//         showToast(message);
//     }
// });
$(document).ready(function () {
    const page = $("body").data("page");
    const message = $("body").data("toast");

    if (!message) return;

    // 아이디 찾기 페이지면 alert만
    if (page === "find-id") {

        // 🔥 핵심: 실제 개행이 아니라 "\n" 문자열 기준
        const lines = message.includes("\\n")
            ? message.split("\\n")
            : message.split("\n");

        const title = lines[0];
        const ids = message.includes("\\n")
            ? message.split("\\n")
            : message.split("\n");

        Swal.fire({
            title: '🔍 고객님의 아이디',
            html: `
        <div style="margin-top:12px; text-align:left;">
            ${ids.map((id, idx) => `
                <div style="
                    background:#2b2622;
                    padding:10px;
                    border-radius:8px;
                    margin-bottom:8px;
                    font-weight:600;
                ">
                    ${idx + 1}. ${id}
                </div>
            `).join("")}
        </div>
    `,
            confirmButtonText: '확인',
            confirmButtonColor: '#ffb84d',
            background: '#1f1b18',
            color: '#ffffff'
        });

    }


});
