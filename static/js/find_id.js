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
$(document).ready(function() {
    
    // 1. 휴대전화 필드 (id="phone_number")에 자동 하이픈 기능 연결
    $('#phone_number').on('input', function() {
        autoHyphenate(this);
    });

    // 2. 생년월일 필드 (id="birthday")에 숫자 필터링 기능 연결
    $('#birthday').on('input', function() {
        filterNumberOnly(this);
    });

});