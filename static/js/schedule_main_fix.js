function activateAddButton() {
    // '추가' 버튼을 활성화 상태로 되돌립니다.
    const $addButton = $(".search-button");
    if ($addButton.prop("disabled")) {
        $addButton.prop("disabled", false).text("추가").css({
            "opacity": 1,
            "cursor": "pointer"
        });
    }
}

$(function(){
    // 모든 드롭다운 요소를 변수로 지정
    const $destDropdown = $("#destinationDropdown");
    const $dateDropdown = $("#calendarDropdown");
    const $tourDropdown = $("#tourDropdown");

    // ============================+
    // 드롭다운 공통 처리
    // ============================
    function hideAllDropdowns() {
        $(".top-search-item").removeClass("active");
        $destDropdown.hide();
        $dateDropdown.hide();
        $tourDropdown.hide();
    }

    // 아이템 클릭 시 해당 드롭다운 토글
    $(".top-search-item").on("click", function(e){
        e.stopPropagation();
        const $item = $(this);
        const $targetDropdown = $item.find(".dropdown-content");

        if ($item.hasClass("active")) {
            hideAllDropdowns();
        } else {
            hideAllDropdowns();
            $item.addClass("active");
            $targetDropdown.show();
        }
    });

    // 바디 클릭 시 모든 드롭다운 닫기
    $(document).on("click", function(){ hideAllDropdowns(); });

    // 드롭다운 내부 클릭 시 버블링 방지
    $(".dropdown-content").on("click", function(e){ e.stopPropagation(); });


    // ============================
    // 1. 여행지 드롭다운 처리
    // ============================
   $(".destination-item").on("click", function(){
    const $item = $(this);
    const selectedText = $item.data('destination'); // 예: "경주시 경상북도"
    const selectedAdmCode = $item.data('code');     // 📌 ADM Code 추출 (추가됨)
    const [city, province] = selectedText.split(' ');
    
    // 1. 상단 표시 업데이트 (기존 로직 유지)
    $("#destinationItem .selected-city").text(city.replace('', ''));
    $("#destinationItem .selected-province").text(province);
    $("#destinationItem .sub-label").text("");

    // 2.  세션 스토리지 업데이트 (ADM Code 및 도시 정보 저장)
    const currentDataJson = sessionStorage.getItem('currentSearchData') || '{}';
    let searchData;
    
    try {
        searchData = JSON.parse(currentDataJson);
    } catch (e) {
        console.error("세션 데이터 파싱 오류:", e);
        searchData = {}; // 파싱 실패 시 초기화
    }
    
    // 필수 키 (adm_code)와 구조화된 정보 (destination) 업데이트
    searchData.adm_code = selectedAdmCode;
    searchData.destination = {
        city: city.replace('', ''),
        province: province
    };
    
    // 세션에 저장
    try {
        sessionStorage.setItem('currentSearchData', JSON.stringify(searchData));
        console.log(" ADM Code가 세션에 저장됨:", selectedAdmCode);
        
        // **중요:** 이 항목에 .selected 클래스를 추가하여 'search-button'에서 읽을 수 있도록 합니다.
        // 하지만 세션에 직접 저장했으므로, 이 클릭 이벤트는 DOM 클래스 대신 세션 저장이 주 목표가 됩니다.
        
    } catch (e) {
        console.error("ADM Code 세션 저장 오류:", e);
    }
    
    // 3. UI 제어 (기존 로직 유지)
    activateAddButton();
    hideAllDropdowns();
});

    // ============================
    // 2. 날짜 (2개 달력) 처리
    // ============================
    let today = new Date();
    let currentMonth = today.getMonth();
    let currentYear = today.getFullYear();
    let startDate = null;
    let endDate = null;
    const $dateDropdownn = $("#calendarDropdown"); // 드롭다운 변수 선언

function formatDate(year, month, day) {
    // ... (기존 formatDate 함수 유지) ...
    return `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
}

// 검색창 UI 업데이트를 위한 새로운 함수
function applySelectedDatesToSearchUI() {

    
    let datesDisplay = '';     // '2025/11/28 - 2025/11/30'
    let durationDisplay = '';  // '2박 3일'

    $("#dateItem .search-label").text("날짜"); 

    // 1. 시작일과 종료일이 모두 선택된 경우 
    if (startDate && endDate) {
        const start = new Date(startDate);
        const end = new Date(endDate);
        const diffTime = Math.abs(end - start);
        const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24)); 
        const nights = diffDays; // 숙박일수 (날짜 차이)
        const days = diffDays + 1; // 여행일수 (날짜 차이 + 1)
        
        // YYYY/MM/DD 형식으로 표시
        const startStr = `${start.getFullYear()}-${start.getMonth() + 1}-${start.getDate()}`;
        const endStr = `${end.getFullYear()}-${end.getMonth() + 1}-${end.getDate()}`;
        
        // **시작일 ~ 종료일 형식으로 표시**
        datesDisplay = `${startStr} ~ ${endStr}`;
        // **기간 표시 (예: 2박 3일)**
        // durationDisplay = `${nights}박 ${days}일`; 
        
        // '날짜 추가' 텍스트를 제거
        $("#dateItem .sub-label").text(""); 

    } 
    // 2. 시작일만 선택된 경우 (단일 날짜 선택)
    else if (startDate) {
        const start = new Date(startDate);
        
        datesDisplay = `${start.getFullYear()}-${start.getMonth() + 1}-${start.getDate()}`;
        durationDisplay = ''; 
        
        // '날짜 추가' 텍스트를 제거
        $("#dateItem .sub-label").text(""); 
    } 
    // 3. 아무것도 선택되지 않은 경우
    else {
        $("#dateItem .sub-label").text("날짜 추가");
        datesDisplay = '';
        durationDisplay = '';
    }

    $("#dateItem .selected-dates").text(datesDisplay);
    $("#dateItem .selected-duration").text(durationDisplay);
}

    function renderCalendar(year, month, containerId, monthId) {
        const monthDate = new Date(year, month, 1);
        const nextMonthDate = new Date(year, month + 1, 1);
        const monthNames = ["1월","2월","3월","4월","5월","6월","7월","8월","9월","10월","11월","12월"];

        $(`#${monthId}`).text(`${year}년 ${monthNames[month]}`);

        const firstDay = monthDate.getDay();
        const daysInMonth = new Date(year, month + 1, 0).getDate();

        let html = "<table><tr>";
        ["일","월","화","수","목","금","토"].forEach(d => html+=`<th>${d}</th>`); html+="</tr><tr>";

        for(let i = 0; i < firstDay; i++) html += "<td></td>";

        for(let day = 1; day <= daysInMonth; day++){
            let dateStr = formatDate(year, month, day);
            let dayDate = new Date(year, month, day);

            let isToday = (today.toDateString() === dayDate.toDateString());
            let isSelected = (startDate === dateStr || endDate === dateStr);

            // 범위 선택 로직 추가 필요: start < dayDate < end
            let isInRange = false;
            if (startDate && endDate) {
                const start = new Date(startDate);
                const end = new Date(endDate);
                
                start.setHours(0, 0, 0, 0);
                end.setHours(0, 0, 0, 0);
                dayDate.setHours(0, 0, 0, 0);

                if (dayDate > start && dayDate < end) {
                    isInRange = true;
                }
            }

            if((firstDay + day - 1) % 7 === 0 && day !== 1) html += "</tr><tr>";
            
            let classes = '';
            if (isToday) classes += 'today ';
            if (isSelected) classes += 'selected ';
            if (isInRange) classes += 'range ';

            html += `<td class="${classes}" data-date="${dateStr}">${day}</td>`;
        }
        html += "</tr></table>";
        $(`#${containerId}`).html(html);
    }

    function updateCalendars() {
        renderCalendar(currentYear, currentMonth, 'calendarContainer1', 'month1');

        let nextMonth = currentMonth + 1;
        let nextYear = currentYear;
        if (nextMonth > 11) { nextMonth = 0; nextYear++; }
        renderCalendar(nextYear, nextMonth, 'calendarContainer2', 'month2');
    }

    // 초기 달력 렌더링
    updateCalendars();

    // 이전/다음 달 버튼 클릭
    $(".prev-month").on("click", function(){
        currentMonth--; if(currentMonth < 0){ currentMonth = 11; currentYear--; }
        updateCalendars();
    });
    $(".next-month").on("click", function(){
        currentMonth++; if(currentMonth > 11){ currentMonth = 0; currentYear++; }
        updateCalendars();
    });

    // 날짜 선택 로직
    $dateDropdown.on("click","td[data-date]",function(){
    const dateStr = $(this).data("date");
    if (!dateStr) return;

    // 시작일/종료일 선택 로직 
    if (!startDate || (startDate && endDate) || new Date(dateStr) < new Date(startDate)) {
        startDate = dateStr;
        endDate = null;
    } else if (dateStr > startDate) {
        // 선택일이 시작일보다 늦으면 -> 종료일 설정
        endDate = dateStr;
    }
    
    updateCalendars(); 
    activateAddButton();
});
    
    // 지우기 버튼
    $(".reset-btn").on("click", function(){
        startDate = null;
        endDate = null;
        $dateDropdown.find("td").removeClass("selected range");
        updateDateDisplay();
        activateAddButton();
    });
    
    // 적용 버튼
    $(".apply-btn").on("click", function(){
        
        applySelectedDatesToSearchUI();
        hideAllDropdowns();
    });

    $(".apply-btn").on("click", function(){
    updateDateDisplay(); 
    hideAllDropdowns();
    });

// ============================
// 추가 버튼 및 세션 저장 처리
// ============================
$(".search-button").on("click", function() {
    const $addButton = $(this);
  
    const $selectedDestination = $("#destinationDropdown .destination-item.selected");
    const admCode = $selectedDestination.length ? $selectedDestination.data('code') : null;
    
    
    const durationText = $("#dateItem .selected-duration").text();
    let durationDays = 0;
    
    if (durationText) {
        const parts = durationText.split(' ');
        if (parts.length > 1 && parts[1].endsWith('일')) {
            try {
                durationDays = parseInt(parts[1].replace('일', ''), 10);
            } catch (e) {
                durationDays = 1;
            }
        } else if (durationText.includes('당일')) {
            durationDays = 1;
        }
    }
    
    const themeTags = Array.from(document.querySelectorAll('.select-btn.selected'))
                          .map(el => el.getAttribute('data-theme'));

    const searchData = {
        adm_code: admCode, 
        duration_days: durationDays, 
        theme_tags: themeTags, 
        destination: {
            city: $("#destinationItem .selected-city").text(),
            province: $("#destinationItem .selected-province").text()
        },
        
        date: {
            startDate: startDate, 
            endDate: endDate, 
            display: $("#dateItem .selected-dates").text(),
            durationText: durationText 
        },
        
        personnel: {
            type: selectedPersonnelType, 
            count: personnelCount, 
            display: `${selectedPersonnelType} ${personnelCount}인`
        }
    };
    
    if (!searchData.adm_code || searchData.duration_days < 1 || searchData.personnel.count < 1 || searchData.theme_tags.length < 2) {
        alert("⚠️ 여행지, 여행일(최소 1일), 인원, 테마(최소 2개)를 모두 선택해주세요.");
        return; 
    }

    try {
        sessionStorage.setItem('currentSearchData', JSON.stringify(searchData));
        console.log("검색 데이터가 세션에 저장되었습니다:", searchData);
    } catch (e) {
        console.error("세션 스토리지 저장 오류:", e);
        alert("데이터 저장 중 오류가 발생했습니다.");
        return;
    }

    // 7. 저장 성공 후 피드백
    $addButton.prop("disabled", true).text("완료").css({
        "opacity": 1,
        "cursor": "default"
    });
    
    alert("검색 조건이 저장되었습니다. 이제 '여행 만들기' 버튼을 눌러주세요.");
});


// ============================
// 페이지 로드 시 상태 확인
// ============================
const savedData = sessionStorage.getItem('currentSearchData');
if (savedData) {
    $(".search-button").prop("disabled", true).text("완료").css({
        "opacity": 1,
        "cursor": "default"
    });
}


// ============================
// 3. 여행 인원 드롭다운 처리 
// ============================
let selectedPersonnelType = '1인'; 
let personnelCount = 1; 

const $paxDropdown = $("#tourDropdown"); 
const $countNumber = $paxDropdown.find("#friendCount"); 
const $countControls = $paxDropdown.find(".count-controls");

function updatePersonnelSearchUI() {
    let nameDisplay = '';
    let countDisplay = '';
    const $searchItem = $("#tourTypeItem");
    
    // 1. 선택이 없는 경우 (지우기)
    if (!selectedPersonnelType) {
        // .sub-label에 '인원 선택' 텍스트를 복구합니다.
        $searchItem.find(".sub-label").text("인원 선택"); 
        $searchItem.find(".selected-personnel-name").text("");
        $searchItem.find(".selected-personnel-count").text("");
        
        return; 
    }
    
    // 2. 선택이 있는 경우
    $searchItem.find(".sub-label").text(""); 
    
    nameDisplay = selectedPersonnelType;
    
    if (personnelCount > 0) {
        countDisplay = `${personnelCount}인`;
    } else {
        countDisplay = '';
        nameDisplay = selectedPersonnelType; 
    }

    $searchItem.find(".selected-personnel-name").text(nameDisplay);
    $searchItem.find(".selected-personnel-count").text(countDisplay);
}


// 탭 클릭 이벤트
$paxDropdown.on("click", ".tour-tab", function() {
    const typeText = $(this).text();
    $paxDropdown.find(".tour-tab").removeClass("active");
    $(this).addClass("active");
    selectedPersonnelType = typeText;
    activateAddButton();
});

// 인원수 (+/-) 버튼 클릭 이벤트
$paxDropdown.on("click", ".count-btn", function() {
    let currentCount = parseInt($countNumber.text());
    
    if ($(this).hasClass('plus-btn')) {
        currentCount++;
    } else if ($(this).hasClass('minus-btn') && currentCount > 0) {
        currentCount--;
    }

    personnelCount = currentCount; 
    $countNumber.text(personnelCount); 
    activateAddButton();
});

// 지우기 버튼
$paxDropdown.on("click", ".reset-btn", function(){
    selectedPersonnelType = null;
    personnelCount = 0;
    
    $paxDropdown.find(".tour-tab").removeClass("active");
    $countNumber.text("0");
    
    updatePersonnelSearchUI();
    activateAddButton();
});
    
//인원 선택사항 업데이트
$(".apply-btn").off("click").on("click", function(){    
    updatePersonnelSearchUI();
    applySelectedDatesToSearchUI(); 
    hideAllDropdowns();
});


personnelCount = 1;
selectedPersonnelType = '1인';

// UI 반영
const $onePersonTab = $paxDropdown.find('.tour-tab').filter(function() {
    return $(this).text() === '1인';
});
$onePersonTab.addClass('active');
$countNumber.text(1);


// updatePersonnelSearchUI();
});


//여행지 검색
document.addEventListener('DOMContentLoaded', function() {
    // ⭐️ 기존 요소들 정의
    const searchInput = document.getElementById('destinationSearchInput');
    const dropdownItems = document.querySelectorAll('#destinationDropdown .destination-item:not(.no-hover)');
    const destinationDropdown = document.getElementById('destinationDropdown');
    const destinationItem = document.getElementById('destinationItem');
    const noResultsMessage = document.getElementById('noResults');

    // ⭐️ 플레이스홀더 및 선택된 지역 표시 요소
    const searchPlaceholder = document.getElementById('searchPlaceholder');
    const selectedCitySpan = document.querySelector('.selected-city');
    const selectedProvinceSpan = document.querySelector('.selected-province');

    // ⭐️ 초기 상태: 검색 입력 필드는 숨기고 플레이스홀더만 보여줍니다.
    if (selectedCitySpan.textContent.trim() === '' && selectedProvinceSpan.textContent.trim() === '') {
        searchPlaceholder.style.display = 'inline';
        searchInput.style.display = 'none'; // 입력 필드 숨김
    } else {
        searchPlaceholder.style.display = 'none';
        searchInput.style.display = 'none'; // 선택되면 입력 필드를 계속 숨김
    }
    destinationDropdown.style.display = 'none'; // 드롭다운 기본 숨김

    // 1. 여행지 검색 영역(top-search-item) 클릭 시: 입력 필드 활성화 및 드롭다운 토글
    destinationItem.addEventListener('click', function(e) {
        // 이미 선택된 항목을 클릭한 경우에는 무시합니다.
        if (e.target.closest('.destination-item')) return;
        
        // 검색 필드를 보여주고 플레이스홀더 숨김 (검색 준비 상태)
        searchPlaceholder.style.display = 'none';
        searchInput.style.display = 'inline-block';
        searchInput.focus(); // 입력 포커스
        
        // 드롭다운 토글
        if (destinationDropdown.style.display === 'block') {
             destinationDropdown.style.display = 'none';
        } else {
            destinationDropdown.style.display = 'block';
        }
    });

    // 2. 검색창 입력 이벤트 (필터링 로직)
    searchInput.addEventListener('input', function() {
        // ... (기존 필터링 로직 유지) ...
        const searchText = searchInput.value.toLowerCase().trim();
        let foundResults = false;

        dropdownItems.forEach(item => {
            const cityName = item.getAttribute('data-city').toLowerCase();
            if (cityName.includes(searchText)) {
                item.style.display = 'block';
                foundResults = true;
            } else {
                item.style.display = 'none';
            }
        });

        if (!foundResults && searchText.length > 0) {
            noResultsMessage.style.display = 'block';
        } else {
            noResultsMessage.style.display = 'none';
        }
        destinationDropdown.style.display = 'block'; // 입력 중에는 드롭다운 유지
    });

    // 3. 드롭다운 항목 클릭 처리 (선택 로직)
    dropdownItems.forEach(item => {
        item.addEventListener('click', function() {
            const fullCityName = this.getAttribute('data-city'); 
            const parts = fullCityName.split(' ');
            const sido = parts[0];
            const sigungu = parts.slice(1).join(' ');

            // ⭐️ 선택 후 처리: 검색 필드와 플레이스홀더를 다시 숨기고 선택된 지역 표시
            
            // 검색 필드 숨김
            searchInput.value = '';
            searchInput.style.display = 'none'; 
            
            // 선택된 지역 표시
            selectedProvinceSpan.textContent = sido;
            selectedCitySpan.textContent = sigungu;
            
            // 드롭다운 닫기
            destinationDropdown.style.display = 'none';
        });
    });

    // 4. 검색창 이외의 영역 클릭 시 숨기기 (수정된 로직)
    document.addEventListener('click', function(event) {
        // 클릭된 영역이 destinationItem (검색바 영역 전체)의 자식이 아닐 경우에만 닫기
        if (!destinationItem.contains(event.target)) {
            destinationDropdown.style.display = 'none';
            
            // ⭐️ 닫을 때 검색 필드 숨기고, 플레이스홀더나 선택 지역 표시로 복귀
            searchInput.style.display = 'none';
            searchInput.value = '';
            
            // 선택된 지역이 없을 경우에만 플레이스홀더를 다시 표시
            if (selectedCitySpan.textContent.trim() === '') {
                 searchPlaceholder.style.display = 'inline';
            }
        }
    });
});

// 여행테마 선택 //
document.addEventListener('DOMContentLoaded', () => {
    const buttons = document.querySelectorAll('.select-btn');
    const minSelection = 2;
    const maxSelection = 4;
    const messageElement = document.getElementById('selection-message');

    // 세션에 테마 데이터를 저장/업데이트하는 함수
    const saveThemesToSession = () => {
        // 현재 선택된 모든 테마의 data-theme 값을 배열로 수집
        const selectedThemes = Array.from(document.querySelectorAll('.select-btn.selected'))
                                    .map(el => el.getAttribute('data-theme'));

        // 기존의 세션 데이터를 불러옵니다. (없으면 빈 객체)
        const currentDataJson = sessionStorage.getItem('currentSearchData') || '{}';
        let searchData;
        try {
            searchData = JSON.parse(currentDataJson);
        } catch (e) {
            console.error("세션 데이터 파싱 오류:", e);
            searchData = {};
        }

        searchData.theme_tags = selectedThemes;

        try {
            sessionStorage.setItem('currentSearchData', JSON.stringify(searchData));
            console.log("테마 정보가 세션에 업데이트되었습니다:", searchData.theme_tags);
        } catch (e) {
            console.error("세션 스토리지 저장 오류:", e);
        }
        
        return selectedThemes.length;
    };

    buttons.forEach(button => {
        button.addEventListener('click', () => {
            const isSelected = button.classList.contains('selected');
            const currentSelected = document.querySelectorAll('.select-btn.selected').length;
            let finalSelected;

            if (isSelected) {
                button.classList.remove('selected');
                finalSelected = saveThemesToSession(); 
                messageElement.textContent = ''; 
            } else {
                if (currentSelected < maxSelection) {
                    button.classList.add('selected');
                    finalSelected = saveThemesToSession(); 
                    messageElement.textContent = ''; 
                } else {
                    messageElement.textContent = `⚠️ 테마는 최대 ${maxSelection}개까지만 선택할 수 있습니다.`;
                    return; 
                }
            }

            // 메시지 업데이트 로직
            if (finalSelected > 0 && finalSelected < minSelection) {
                messageElement.textContent = `⚠️ 테마는 최소 ${minSelection}개 이상 선택해야 합니다. (현재 ${finalSelected}개)`;
                messageElement.style.color = 'red'; // 색상 강조
            } else if (finalSelected >= minSelection) {
                messageElement.textContent = `✅ ${finalSelected}개의 테마가 선택되었습니다.`;
                messageElement.style.color = 'green';
            } else {
                messageElement.textContent = '';
            }
        });
    });
});


// 여행만들기 start

$(document).ready(function() {
    // 1. 세션 스토리지에서 저장된 검색 데이터 가져오기
    const savedSearchDataJSON = sessionStorage.getItem('currentSearchData');
    let savedCity = ''; 

    if (savedSearchDataJSON) {
        try {
            const searchData = JSON.parse(savedSearchDataJSON);
            // 'destination.city' 경로에서 도시 이름을 추출합니다.
            savedCity = searchData.destination.city || '';
        } catch (e) {
            console.error("저장된 검색 데이터 파싱 오류:", e);
        }
    }
    
    // City 이름이 있다면 템플릿에 사용할 접두사 생성
    const cityPrefix = savedCity ? `[${savedCity}] ` : '추천 ';


    // // 3. '여행 만들기' 버튼 클릭 이벤트 내에서 제목 수정 적용
$('.button-make-travel').on('click', function(e) {
    e.preventDefault(); 

    const $resultArea = $('#result-area');
    // 로딩 메시지 표시
    $resultArea.html('<p style="text-align: center; color: #5B8B7B; font-weight: bold;">여행을 만드는 중입니다...</p>');

    // 1. 세션 스토리지에서 검색 데이터 불러오기
    const searchDataJson = sessionStorage.getItem('currentSearchData');
    if (!searchDataJson) {
        $resultArea.html('<p style="text-align: center; color: red;">⚠️ 검색 데이터가 세션에 없습니다. 다시 선택해주세요.</p>');
        return;
    }
    
    let requestData;
    try {
        requestData = JSON.parse(searchDataJson);
    } catch (error) {
        $resultArea.html('<p style="text-align: center; color: red;"> 데이터 로드 중 오류가 발생했습니다.</p>');
        console.error("세션 데이터 파싱 오류:", error);
        return;
    }

    // 2. ADM 코드 유효성 검사 (필수 입력값)
    const admCode = requestData.adm_code; 
    if (!admCode) {
        $resultArea.html('<p style="text-align: center; color: red;"> 여행지가 선택되지 않았습니다.</p>');
        return;
    }
    
    const cityPrefix = requestData.destination && requestData.destination.city 
                       ? requestData.destination.city 
                       : '추천';
    
    // 3. 실제 AJAX 요청 (fetch API 사용 , 비동기)
    fetch('/schedule/recommend', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestData)
    })
    .then(response => {
        // HTTP 응답 상태 확인
        if (!response.ok) {
            throw new Error(`서버 응답 오류: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        // 4. 응답 데이터 처리 및 HTML 렌더링
        if (data.success && data.recommended_trips) {
            
            const recommendedTrips = data.recommended_trips;
            
            if (recommendedTrips.length === 0) {
                 $resultArea.html(`
                    <p style="text-align: center; color: #333; font-weight: bold;">
                        선택하신 조건(${cityPrefix})에 맞는 여행지를 찾지 못했습니다.
                    </p>
                `);
                return;
            }

            // 5. HTML 리스트 생성 시작
            let listHtml = `
                <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 20px;">
                    <h3 style="color: #333; margin: 0;">${cityPrefix} 추천 여행 리스트</h3>
                    <button class="reload-btn">추천 다시 받기</button>
                </div>
            `;
            
            recommendedTrips.forEach(trip => {
                const title = `${cityPrefix}` + "여행";
                const displayCity = `${trip.SIDO_NM || ''} ${cityPrefix || ''}`; 
                const rating = (trip.SCORE ).toFixed(1);  // 별점
                const tags = trip.TAGS ? trip.TAGS.split(',') : ['추천', '여행']; //태그
                const scheduleItems = trip.RELATED_PLACES;
                const currentTripId = trip.CONTENT_ID;
                const scheduleHtml = scheduleItems.map(place => {
                return `<div class="schedule-place-item" data-place-id="${place.id}">${place.name}</div>`; 
                }).join(' → ');

                listHtml += `
                    <div class="trip-item" data-trip-id="${currentTripId}">
                        <div class="trip-header-line"> 
                            <h4>${title}</h4>
                            <p class="trip-meta">${displayCity} | ${trip.DURATION}일</p> 
                            <p class="trip-rating">⭐ ${rating}</p>
                        </div>
                        
                        <div class="trip-schedule-container">${scheduleHtml}  </div>
                        
                        <div class="trip-tags">
                            <div class="tag-group"> 
                                ${tags.map(tag => `<span>#${tag}</span>`).join('')}
                            </div>
                        </div>

                    </div>
                `;
            });

            listHtml += '<div class="detail-container" data-trip-id="${currentTripId}"><a href="/schedule/view/" class="detail-btn">선택</a></div>'; 
            $resultArea.html(listHtml);

            
            $resultArea.on('click', '.trip-item', function(){
                //선택한 요소 외에 비활성화
                $resultArea.find('.trip-item.selected').removeClass('selected');
                //선택요소 강조
                $(this).addClass('selected');
                alert("여행리스트가 선택되었습니다.")
            })

            $resultArea.on('click', '.detail-btn', function(e){
                e.preventDefault();
                const $tripItem = $resultArea.find('.trip-item.selected');
                   if($tripItem.length === 0){
                    alert("여행리스트를 선택해주세요.")
                    return;
                }
                
                // const tripId = $tripItem.data('trip-id');    
                // //None 으로 뜨는것 확인 원인 확인 원인확인후 아래 tripId 선언을 위에 내용으로 변경
                const tripId = 123
                // tripId의 .schedule-place-item class를 찾아서 그 값 자신(this)의 data-place-id의 값을 map으로 작성하고
                // selectedPlaceIds에 그 값을 넣는다.
                const selectedPlaceIds = $tripItem.find(".schedule-place-item").map(function() {
                    return $(this).data("place-id")
                }).get();
                alert("selectedPlaceIds:" + selectedPlaceIds);
                console.log("가져온 Trip ID:", tripId); 
                console.log("가져온 Place ID:", selectedPlaceIds);

                // 3. 유효성 검사 및 이동
                // ⭐️ tripId가 null, undefined, 0, 또는 빈 문자열이거나 'undefined' 문자열인 경우도 체크
                if (!tripId || String(tripId).toLowerCase() === 'undefined') { 
                    alert("트립 ID를 찾을 수 없습니다. (HTML 구조 확인 필요)");
                    console.error("Trip ID 누락!");
                    return;
                }
                
                // 장소 ID는 해시 값(문자열)이므로, 공백이거나 없으면 안됨
                if (!selectedPlaceIds || String(selectedPlaceIds).trim() === '') {
                    alert("선택된 장소 ID가 없습니다.");
                    console.error("Place ID 누락!");
                    return;
                }

                const targetUrl = `/schedule/view/${tripId}`;
                console.log("페이지 이동:", targetUrl);
                window.location.href = targetUrl;
            })
            
        } else {
            $resultArea.html(`<p style="text-align: center; color: red;">추천 실패: ${data.error || data.message || '알 수 없는 오류'}</p>`);
        }
    })
    .catch(error => {
        // 통신 오류 처리
        $resultArea.html('<p style="text-align: center; color: red;">서버 통신 중 심각한 오류가 발생했습니다.</p>');
        console.error('Fetch Error:', error);
    });
});

});