

var mapContainer = document.getElementById('map'), // 지도를 표시할 div 
        mapOption = { 
            center: new kakao.maps.LatLng(35.815967, 127.147255), // 지도의 중심좌표 (전주 인근)
            level: 7 // 지도의 확대 레벨
        };

    // 지도를 표시할 div와 지도 옵션으로 지도를 생성합니다
    var map = new kakao.maps.Map(mapContainer, mapOption); 
    
    var mapTypeControl = new kakao.maps.MapTypeControl();

    // 지도에 컨트롤을 추가
    map.addControl(mapTypeControl, kakao.maps.ControlPosition.TOPRIGHT);

    // 지도 확대 축소를 제어할 수 있는 줌 컨트롤 생성
    var zoomControl = new kakao.maps.ZoomControl();
    map.addControl(zoomControl, kakao.maps.ControlPosition.RIGHT);

    
    var marker = new kakao.maps.Marker();

    // 타일 로드가 완료되면 지도 중심에 마커를 표시합니다
    kakao.maps.event.addListener(map, 'tilesloaded', displayMarker);

    function displayMarker() {
        
        // 마커의 위치를 지도중심으로 설정합니다 
        marker.setPosition(map.getCenter()); 
        marker.setMap(map); 

        // kakao.maps.event.removeListener(map, 'tilesloaded', displayMarker);
    }

// 모달창
document.addEventListener('DOMContentLoaded', function() {
    // 1. 필요한 요소들을 ID로 가져오기 (모달 제어)
    const editBtn = document.getElementById("popupbtn"); // "일정편집" 버튼
    const modal = document.getElementById("modalwrap");  // 모달 전체
    const closeBtn = document.getElementById("closebtn"); // 모달 닫기 버튼
    const listDelBtn = document.getElementById("list-del-btn"); //메인삭제버튼

    // 2. 나타나야 할 요소들을 클래스로 가져오기 (편집 모드 제어)
    const deleteBtns = document.querySelectorAll(".delete-btn"); // 각 일정의 삭제 버튼
    // 일정 추가 버튼을 감싸는 div (숨김 처리된 .timeline-item)
    const addScheduleItems = document.querySelectorAll(".timeline-item.hidden"); 
    const addScheduleBtns = document.querySelectorAll(".add-schedule-btn"); // + 일정 추가 버튼

    // ==========================================================
    // A. "일정 편집" 토글 로직 (편집 모드 ON/OFF)
    // ==========================================================
    if (editBtn) {
        editBtn.onclick = function(e) {
            e.preventDefault();
            
            // 현재 상태가 '일정편집'인지 확인 (편집 모드 진입 시)
            const isEnteringEditMode = editBtn.textContent.includes('일정편집');

            // 1. 버튼 텍스트 토글: '일정편집' <-> '편집 완료'
            editBtn.textContent = isEnteringEditMode ? '편집 완료' : '일정편집';

            // 2. 삭제 버튼 토글 (hidden 클래스 제거/추가)
            // isEnteringEditMode가 true일 때 hidden을 제거하고 (보이게), false일 때 hidden을 추가합니다 (숨기게).
            deleteBtns.forEach(btn => {
                btn.classList.toggle('hidden', !isEnteringEditMode);
            });

            // 3. '+ 일정 추가' 버튼 영역 토글
            addScheduleItems.forEach(item => {
                // '.timeline-item'의 'hidden' 클래스 토글
                item.classList.toggle('hidden', !isEnteringEditMode);
                
                // 내부 '.list-add' div의 'hidden' 속성도 토글
                const listAddDiv = item.querySelector('.list-add');
                if (listAddDiv) {
                    listAddDiv.toggleAttribute('hidden', !isEnteringEditMode); 
                }
            });
        };
    }

    // ==========================================================
    // B. "+ 일정 추가" 버튼 로직 (모달 호출)
    // ==========================================================
    addScheduleBtns.forEach(btn => {
        btn.onclick = function(e) {
            e.preventDefault();
            // 모달을 표시
            if (modal) {
                modal.style.display = "block";
            }
        };
    });
    // ==========================================================
    // D. 일정 편집 삭제버튼 얼럿
    // ==========================================================
    if (deleteBtns.length > 0) {
        deleteBtns.forEach(btn => {
            btn.onclick = function(e) {
                e.preventDefault(); // 버튼 클릭 시 기본 동작(예: 페이지 이동) 방지
                
                const scheduleName = this.closest('.details').querySelector('h4').textContent;
                
                if (confirm(`'${scheduleName}' 일정을 정말로 삭제하시겠습니까?`)) {
                    alert(`${scheduleName} 일정을 삭제합니다.`);
                } else {
                    alert("삭제가 취소되었습니다.");
                }
            };
        });
    }

    // ==========================================================
    // D-2. 전체 일정 목록 삭제 버튼 얼럿
    // ==========================================================
    if (listDelBtn) {
        listDelBtn.onclick = function(e) {
            e.preventDefault(); // 기본 페이지 이동을 막습니다.
            
            // 전체 일정에 대한 확인 메시지
            if (confirm("이 전체 여행 일정을 정말로 삭제하고 목록으로 돌아가시겠습니까?")) {
                alert("전체 일정을 삭제하고 목록으로 이동합니다.");
                
                // 🚨 여기에 서버에 전체 일정 삭제 요청을 보내는 실제 fetch 로직이 들어갑니다.
                // 예시: deleteEntireSchedule(scheduleId).then(() => { window.location.href = this.href; });
                
                // 서버 통신이 성공했다고 가정하고 페이지 이동 실행
                window.location.href = this.href; 
            } else {
                alert("삭제가 취소되었습니다.");
            }
        };
    }
    // ==========================================================
    // C. 모달 닫기 로직
    // ==========================================================
    if (closeBtn && modal) {
        closeBtn.onclick = function(){
            modal.style.display = "none";
        };
        window.onclick = function (event){
            if(event.target === modal){
                modal.style.display = "none";
            }
        };
    }
});



//PDF 


 $(document).ready(function(){
    const tripDataElement = $('#trip-data')[0];
    let encodedMetaString = tripDataElement?.dataset?.tripMeta || '';
    let tripMeta = {};

    if (encodedMetaString) {
        try {
            // 1단계: Flask의 quote_plus가 생성한 '+' 문자를 공백으로 치환합니다.
            const stringWithSpaces = encodedMetaString.replace(/\+/g, ' '); 
            
            // 🚨🚨🚨 수정: 치환된 문자열(stringWithSpaces)을 디코딩합니다.
            const decodedMetaString = decodeURIComponent(stringWithSpaces); 
            
            // 2단계: trim을 수행
            const trimmedMetaString = decodedMetaString.trim();

            if (trimmedMetaString && trimmedMetaString !== '{}') {
                // 3차: JSON 파싱 시도
                tripMeta = JSON.parse(trimmedMetaString); 
            }
            
            // 🚨🚨🚨 성공적으로 파싱된 데이터를 콘솔에 출력하여 확인
            if(Object.keys(tripMeta).length !== 0) {
                 console.log("✅✅✅ 트립정보 (로딩 성공):", tripMeta);
                 
                 // 화면에 데이터 뿌리기 (디버깅용)
                 $('#trip-title').text(tripMeta.title);
                 $('#trip-city').text(`- 여행지역 | ${tripMeta.city}`);
                 // ... (나머지 데이터 출력 로직) ...
            } else {
                 throw new Error("파싱은 성공했으나 객체가 비어있음");
            }
            
        } catch (e) {
            console.error("🚨🚨🚨 치명적 오류: JSON 또는 URL 디코딩 실패. ", e);
            console.log("읽어온 원본 URL 인코딩 문자열:", encodedMetaString);
            // 디코딩 단계까지는 성공했는지 확인하기 위해 출력
            if (typeof decodedMetaString !== 'undefined') {
                 console.log("디코딩된 문자열 (한글이 깨지지 않았는지 확인):", decodedMetaString);
            }
            
            tripMeta = {};
        }
    }
    if(Object.keys(tripMeta).length !== 0){
        console.log("트립정보", tripMeta);

        $('#trip-title').text(tripMeta.title);
        $('#trip-city').text(`- 여행지역 | ${tripMeta.city}`);
        $('#trip-duration').text(`${tripMeta.duration}일`);
        $('#trip-startDate').text(tripMeta.startDate);
        $('#trip-endDate').text(tripMeta.endDate);
        $('#trip-people').text(`인원: ${tripMeta.people || 0}명`);
        $('#trip-tags').text(`테마: ${tripMeta.tags.join(', ') || '없음'}`);           
    
        } else {
            console.log("db에 정보가 없습니다.");
        }
        
        // URL에서 Trip ID 가져오기 (기존 로직 유지)
        const urlParts = window.location.pathname.split('/');
        const tripIdFromUrl = urlParts[3];
    
    if (tripIdFromUrl) {
        console.log("현재 View 페이지의 Trip ID::", tripIdFromUrl);
    }
  });
