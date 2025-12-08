let isIdChecked = false;    // 아이디 중복확인 버튼 눌렀는가
let isIdAvailable = false;  // 사용 가능한 아이디인가

// --- 전화번호 자동 하이픈 포맷팅 함수 ---
function autoHyphenate(input) {
    // 숫자만 추출합니다.
    let number = input.value.replace(/[^0-9]/g, "");
    let temp = "";

    if (number.length < 4) {
        // 3자리 이하 (예: 010)
        temp += number;
    } else if (number.length < 8) {
        // 4~7자리 (예: 010-123)
        temp += number.substr(0, 3);
        temp += "-";
        temp += number.substr(3);
    } else {
        // 8자리 이상 (예: 010-1234-5678)
        temp += number.substr(0, 3);
        temp += "-";
        temp += number.substr(3, 4);
        temp += "-";
        temp += number.substr(7, 4);
    }
    
    input.value = temp;
}
/**
 * 아이디 입력값에서 영문자(a-z, A-Z)만 허용하고 나머지는 제거합니다.
 * @param {HTMLInputElement} input - 아이디 입력 필드 요소
 */
function filterEnglishOnly(input) {
    // [^a-zA-Z] : 영문자(대소문자)가 아닌 모든 문자를 제거
    let filteredValue = input.value.replace(/[^a-zA-Z]/g, '');
    
    // 값이 변경된 경우에만 업데이트
    if (input.value !== filteredValue) {
        input.value = filteredValue;
    }
}

/**
 * 생년월일 입력값에서 숫자(0-9)만 허용하고 나머지는 제거합니다.
 * @param {HTMLInputElement} input - 생년월일 입력 필드 요소
 */
function filterNumberOnly(input) {
    // [^0-9] : 숫자가 아닌 모든 문자를 제거하는 정규 표현식
    let filteredValue = input.value.replace(/[^0-9]/g, '');
    
    // 값이 변경된 경우에만 입력 필드를 업데이트합니다.
    if (input.value !== filteredValue) {
        input.value = filteredValue;
    }
}

/**
 * 사용자 정의 모달을 표시합니다.
 * @param {string} message - 표시할 메시지
 */
function alertModal(message) {
    let modal = document.getElementById('custom-modal');
    if (!modal) {
        modal = document.createElement('div');
        modal.id = 'custom-modal';
        modal.className = 'fixed inset-0 bg-gray-600 bg-opacity-75 flex items-center justify-center z-50 transition-opacity duration-300 opacity-0 pointer-events-none';
        modal.innerHTML = `
            <div class="bg-white p-6 rounded-lg shadow-2xl max-w-sm w-full transform scale-95 transition-transform duration-300">
                <p id="modal-message" class="text-gray-700 text-lg mb-6 whitespace-pre-wrap"></p>
                <button id="modal-ok-btn" class="w-full py-2 bg-indigo-600 text-white font-semibold rounded-lg hover:bg-indigo-700 transition duration-150">확인</button>
            </div>
        `;
        document.body.appendChild(modal);
        document.getElementById('modal-ok-btn').addEventListener('click', () => {
            modal.classList.add('opacity-0', 'pointer-events-none');
            modal.querySelector('div').classList.replace('scale-100', 'scale-95');
        });
    }
    
    document.getElementById('modal-message').textContent = message;
    modal.querySelector('div').classList.replace('scale-95', 'scale-100');
    modal.classList.remove('opacity-0', 'pointer-events-none');
}




// jQuery 호환 유틸리티 함수

/**
 * 폼 제출 버튼의 활성화 상태를 업데이트합니다.
 */
function updateSubmitButtonState() {
    const $form = $('#signup_form');
    let requiredFieldsFilled = true;
    let isPasswordMatch = false;

    // 1. 필수 필드 검사
    $form.find('[required]').each(function() {
        const $el = $(this);
        if ($el.val().trim() === '' && $el.attr('type') !== 'hidden') {
            requiredFieldsFilled = false;
            return false; // break loop
        }
        // Hidden input (성별/국적) 검사
        if ($el.attr('type') === 'hidden' && $el.val().trim() === '') {
            requiredFieldsFilled = false;
            return false; // break loop
        }

        // 5. 📢 이용약관 동의 확인 (새로 추가된 JS 로직)
        if (isValid && !$('#terms_agree').is(':checked')) {
            // 경고 메시지를 사용자에게 보여줍니다.
            alert('이용약관 및 개인정보 처리방침에 동의해야 합니다.');
            // 체크박스에 포커스 (선택 사항)
            $('#terms_agree').focus();
            isValid = false;
        }
        
        if (!isValid) {
            e.preventDefault(); // 유효성 검사 실패 시 폼 제출 방지
        }
    });

    if (isValid && !$('#terms_agree').is(':checked')) {
    alert('이용약관 및 개인정보 처리방침에 동의해야 합니다.');
    $('#terms_agree').focus();
    isValid = false;
    }
    // 2. 비밀번호 일치 검사
    const password = $('#password').val();
    const confirm = $('#password_confirm').val();
    if (password && confirm && password === confirm) {
        isPasswordMatch = true;
        $('#password_match_message').addClass('hidden');
    } else if (confirm.length > 0) {
            // 입력값이 있고 일치하지 않을 때만 메시지 표시
            $('#password_match_message').text('비밀번호가 일치하지 않습니다.').removeClass('hidden').removeClass('text-green-600').addClass('text-red-500');
    } else {
            $('#password_match_message').addClass('hidden');
    }


    // 3. 최종 상태 결정 
    const canSubmit = requiredFieldsFilled && isIdAvailable && isPasswordMatch;
    const $submitBtn = $('#submit_btn');

    if (canSubmit) {
        $submitBtn.prop('disabled', false);
        $submitBtn.removeClass('bg-indigo-400');
        $submitBtn.addClass('bg-indigo-600 hover:bg-indigo-700');
    } else {
        $submitBtn.prop('disabled', true);
        $submitBtn.removeClass('bg-indigo-600 hover:bg-indigo-700');
        $submitBtn.addClass('bg-indigo-400');
    }
}
        
      

    $('#phone_number').on('input', function() {
        // 1. 자동 하이픈 포맷팅 실행
        autoHyphenate(this); 
        
        // 2. 폼 유효성 상태 업데이트 (required 조건 검사)
        updateSubmitButtonState();
    });


    $('#birthday').on('input', function() {
        // 1. 숫자만 허용하도록 필터링 실행
        filterNumberOnly(this); 
        
        // 2. 폼 상태 업데이트 (8자리가 아니면 required에 걸려 버튼 비활성화됨)
        updateSubmitButtonState();
        
        // (선택적) 8자리가 아닌 경우 사용자에게 메시지 표시 로직 추가 가능
    });

    
    // --- 2. 성별 및 국적 버튼 선택 로직 (순수 JS에서 jQuery로 변경) ---
    // 공통 함수: 선택 상태를 토글하고 숨겨진 입력 필드(Hidden Input)를 업데이트
    function toggleSelection($container, hiddenInputId) {
        $container.on('click', '.select-btn', function() {
            const $this = $(this);
            const value = $this.data('value');
            
            // 1. 같은 그룹 내의 모든 버튼에서 선택 클래스 제거 (CSS는 HTML/CSS에 의존)
            $container.find('.select-btn').removeClass('selected');

            // 2. 클릭된 버튼에만 선택 클래스 추가
            $this.addClass('selected');

            // 3. 숨겨진 입력 필드에 data-value 값을 저장 (서버 전송용)
            $('#' + hiddenInputId).val(value);
            
            // 4. 상태 업데이트
            updateSubmitButtonState();
        });
    }

    // 성별 버튼 컨테이너에 이벤트 리스너 등록
    const $genderButtonsContainer = $('#gender-buttons');
    if ($genderButtonsContainer.length) {
        toggleSelection($genderButtonsContainer, 'selected-gender');
    }

    // 국적 버튼 컨테이너에 이벤트 리스너 등록
    const $nationButtonsContainer = $('#nation-buttons');
    if ($nationButtonsContainer.length) {
        toggleSelection($nationButtonsContainer, 'selected-nation');
    }

    setupThemeSelection();
    
    // --- 3. 아이디 중복 확인 및 폼 유효성 검사 로직 ---

    // 3-1. 아이디 입력값이 변경되면 상태를 초기화
    $('#user_id').on('input', function() {
        filterEnglishOnly(this); 
        isIdChecked = false;
        isIdAvailable = false;
        // 메시지 초기화
        $('#id_check_message').text('아이디는 영문자로 입력하세요').removeClass('text-green-600 text-red-500 text-yellow-600').addClass('text-gray-500');
        updateSubmitButtonState();
    });
    
    // 비밀번호 입력 시 실시간 유효성 검사 연결
    $('#password, #password_confirm').on('input', updateSubmitButtonState);
    
    // 기타 모든 입력 필드에 대해 상태 업데이트 연결
    $('.signup-form input').on('input', updateSubmitButtonState);

    // 3-2. 중복 확인 버튼 클릭 이벤트
    $('#check_duplicate_btn').on('click', function() {
        const userId = $('#user_id').val().trim();
        const $message = $('#id_check_message');
        const $btn = $(this);

        if (userId.length < 4) {
            $message.text('아이디는 최소 3자 이상이여야 합니다~!').removeClass('text-green-600').addClass('text-red-500');
            isIdChecked = false;
            isIdAvailable = false;
            updateSubmitButtonState();
            return;
        }
        
        // AJAX 요청 시작: 버튼 비활성화 및 메시지 업데이트
        $btn.prop('disabled', true).text('확인 중...');
        $message.text('아이디 중복 확인 중...').removeClass('text-red-500 text-green-600').addClass('text-gray-500');

        const reservedIds = ["admin", "testuser", "tripmocha"];
        const isDuplicate = reservedIds.includes(userId.toLowerCase());
        
        // Mock AJAX (지연 시간 시뮬레이션)
        setTimeout(() => {
            $btn.prop('disabled', false).text('중복 확인');
            isIdChecked = true; // 확인 작업 완료
            
            if (isDuplicate) {
                $message.text('이미 사용 중인 아이디입니다.').removeClass('text-green-600').addClass('text-red-500');
                isIdAvailable = false; // 사용 불가
            } else {
                $message.text('사용 가능한 아이디입니다!').removeClass('text-red-500 text-gray-500').addClass('text-green-600 font-semibold');
                isIdAvailable = true; // 사용 가능
            }
            updateSubmitButtonState();

        }, 800); // 800ms 지연
    });

// ---------------------------------------------
// 6. 주소 검색 기능 (행정안전부 API 방식)
// ---------------------------------------------
$('#search_address_btn').on('click', function () {
    new daum.Postcode({
        oncomplete: function (data) {
            let addr = data.userSelectedType === 'R'
                ? data.roadAddress
                : data.jibunAddress;

            let extraAddr = '';

            if (data.bname !== '' && /[동|로|가]$/.test(data.bname)) {
                extraAddr += data.bname;
            }
            if (data.buildingName !== '' && data.apartment === 'Y') {
                extraAddr += (extraAddr !== '' ? ', ' + data.buildingName : data.buildingName);
            }
            if (extraAddr !== '') {
                addr += ' (' + extraAddr + ')';
            }

            $('#postcode').val(data.zonecode);
            $('#address').val(addr);
            $('#detail_address').focus();
        }
    }).open();
});


    // 3-3. 폼 제출 시 최종 유효성 검사 (가입하기 버튼 클릭 시)
    $('.signup-form').on('submit', function(e) {
        // 아이디 중복 확인 필수 검증
        if (!isIdChecked || !isIdAvailable) {
            e.preventDefault(); // 폼 제출 막기
            // 사용자 요청 코드의 alert()를 alertModal()로 변경
            alertModal('아이디 중복 확인이 필요하며, 사용 가능한 아이디여야 합니다.'); 
            $('#user_id').focus();
            return;
        }
        
        // updateSubmitButtonState가 비밀번호 일치와 모든 필드 검사를 미리 수행했지만, 
        // 최종 제출 시점에 다시 한번 확인합니다.
        if ($('#password').val() !== $('#password_confirm').val()) {
                e.preventDefault(); 
                alertModal('비밀번호와 비밀번호 확인이 일치하지 않습니다.');
                return;
        }
        
        // 폼 데이터 수집 및 시뮬레이션
        e.preventDefault();
        const formData = new FormData(this);
        const data = {};
        formData.forEach((value, key) => data[key] = value);

        console.log("폼 데이터:", data);


        console.log("회원가입 성공. 로그인 페이지로 이동합니다."); 
        
        // Flask에서 정의된 로그인 페이지 경로로 즉시 이동
        window.location.href = '/login'; 
        
        // return을 추가하여 혹시 모를 추가 코드 실행을 방지
        return;

    });
// jQuery 호환 유틸리티 함수

function updateSubmitButtonState() {
    const $form = $('#signup_form'); // 폼 ID는 'signup_form'으로 가정
    let requiredFieldsFilled = true;
    let isPasswordMatch = false;

    // 1. 필수 필드 검사
    // (이 부분은 기존 코드를 그대로 유지하여 모든 required 필드를 검사합니다.)
    $form.find('[required]').each(function() {
        const $el = $(this);
        // ... 기존 필수 필드 검사 로직 ...
        if (($el.attr('type') !== 'hidden' && $el.val().trim() === '') || 
            ($el.attr('type') === 'hidden' && $el.val().trim() === '')) {
            requiredFieldsFilled = false;
            return false; // break loop
        }
    });

    // 2. 비밀번호 일치 검사 (
    const password = $('#password').val();
    const confirm = $('#password_confirm').val();
    const $matchMessage = $('#password_match_message');
    
    // 비밀번호 필드 중 하나라도 비어있으면 메시지를 숨깁니다.
    if (!password || !confirm) {
        $matchMessage.addClass('hidden');
    } else if (password === confirm) {
        // 일치할 경우: 성공 메시지를 표시하고 상태를 true로 설정
        isPasswordMatch = true;
        $matchMessage.text('비밀번호가 일치합니다.').removeClass('text-red-500').addClass('text-green-600').removeClass('hidden');
    } else {
        // 불일치할 경우: 오류 메시지를 표시하고 상태를 false로 설정
        isPasswordMatch = false;
        $matchMessage.text('비밀번호가 일치하지 않습니다.').removeClass('text-green-600').addClass('text-red-500').removeClass('hidden');
    }


    // 3. 최종 상태 결정 (ID 확인은 jQuery 스크립트의 전역 변수 isIdAvailable 사용)
    // isIdAvailable은 jQuery $(document).ready 블록 안에서 선언되어야 합니다.
    const canSubmit = requiredFieldsFilled && isIdAvailable && isPasswordMatch;
    const $submitBtn = $('#submit_btn');

    if (canSubmit) {
        $submitBtn.prop('disabled', false);
        $submitBtn.removeClass('bg-indigo-400').addClass('bg-indigo-600 hover:bg-indigo-700');
    } else {
        $submitBtn.prop('disabled', true);
        $submitBtn.removeClass('bg-indigo-600 hover:bg-indigo-700').addClass('bg-indigo-400');
    }
}

// =======================================================
// D. 여행 테마 선택 관리 함수
// =======================================================

function setupThemeSelection() {
    const maxThemes = 3;
    const $themesContainer = $('#theme-buttons');
    const $hiddenInput = $('#selected-themes');
    const $message = $('#theme-message');

    $themesContainer.on('click', '.theme-select-btn', function() {
        const $this = $(this);
        const isSelected = $this.hasClass('selected');
        
        let selectedThemes = $hiddenInput.val().split(',').filter(t => t.trim() !== '');
        
        if (isSelected) {
            // 선택 해제: 배열에서 테마 제거
            $this.removeClass('selected');
            selectedThemes = selectedThemes.filter(theme => theme !== $this.data('value'));
        } else {
            // 선택: 최대 개수 확인
            if (selectedThemes.length >= maxThemes) {
                
                return; // 추가 선택 방지
            }
            // 선택 추가: 배열에 테마 추가
            $this.addClass('selected');
            selectedThemes.push($this.data('value'));
        }

        // 숨겨진 필드 업데이트 (콤마로 구분하여 저장)
        $hiddenInput.val(selectedThemes.join(','));
        
        // 메시지 및 유효성 검사 업데이트
        if (selectedThemes.length < 3) {
            $message.text(`최소 3개의 테마를 선택해야 합니다. (현재 ${selectedThemes.length}개 선택)`).removeClass('hidden text-green-600').addClass('text-red-500');
            $hiddenInput.prop('required', true); // 3개 미만이면 필수 유지
        } else {
            $message.text(`테마 선택 완료!`).removeClass('hidden text-red-500').addClass('text-green-600');
            // 필수는 3개 미만일 때만 체크하도록 처리 (혹시 모를 오류 방지)
        }
        
        // 최종 상태 업데이트 (폼 제출 버튼 활성화/비활성화)
        updateSubmitButtonState();
    });
}


// ===============================
// 선호 여행 스타일 선택 (최대 4개)
// ===============================
function setupTravelStyleSelection() {
    const maxCount = 4;
    const selectedSet = new Set();  // 중복 방지용

    $(".style-btn").on("click", function () {
        const value = $(this).data("value");

        // 이미 선택된 버튼이면 해제
        if ($(this).hasClass("selected")) {
            $(this).removeClass("selected");
            selectedSet.delete(value);
        } else {
            // 새로 선택인데 이미 4개면 막기
            if (selectedSet.size >= maxCount) {
                alert("최대 4개까지만 선택할 수 있습니다.");
                return;
            }
            $(this).addClass("selected");
            selectedSet.add(value);
        }

        // hidden input에 "a,b,c" 형태로 저장
        $("#travel_style").val(Array.from(selectedSet).join(","));
    });
}

// 여행 테마
document.addEventListener("DOMContentLoaded", function () {
    const buttons = document.querySelectorAll(".style-btn");
    let selectedCount = 0;
    const maxSelect = 4;

    buttons.forEach(btn => {
        btn.addEventListener("click", function () {

            // 선택 해제
            if (btn.classList.contains("selected")) {
                btn.classList.remove("selected");
                selectedCount--;
                return;
            }

            // 선택 제한
            if (selectedCount >= maxSelect) {
                alert("4개까지만 선택할 수 있어요!");
                return;
            }

            // 새로 선택
            btn.classList.add("selected");
            selectedCount++;
        });
    });
});
