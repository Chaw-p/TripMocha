

// var mapContainer = document.getElementById('map'), // 지도를 표시할 div 
//         mapOption = { 
//             center: new kakao.maps.LatLng(35.815967, 127.147255), // 지도의 중심좌표 (전주 인근)
//             level: 7 // 지도의 확대 레벨
//         };

//     // 지도를 표시할 div와 지도 옵션으로 지도를 생성합니다
//     var map = new kakao.maps.Map(mapContainer, mapOption); 
    
//     var mapTypeControl = new kakao.maps.MapTypeControl();

//     // 지도에 컨트롤을 추가
//     map.addControl(mapTypeControl, kakao.maps.ControlPosition.TOPRIGHT);

//     // 지도 확대 축소를 제어할 수 있는 줌 컨트롤 생성
//     var zoomControl = new kakao.maps.ZoomControl();
//     map.addControl(zoomControl, kakao.maps.ControlPosition.RIGHT);

    
//     var marker = new kakao.maps.Marker();

//     // 타일 로드가 완료되면 지도 중심에 마커를 표시합니다
//     kakao.maps.event.addListener(map, 'tilesloaded', displayMarker);

//     function displayMarker() {
        
//         // 마커의 위치를 지도중심으로 설정합니다 
//         marker.setPosition(map.getCenter()); 
//         marker.setMap(map); 

//         // kakao.maps.event.removeListener(map, 'tilesloaded', displayMarker);
//     }

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
            document.getElementById('modalbody').dataset.day = this.dataset.day

            
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
    // if (deleteBtns.length > 0) {
    //     deleteBtns.forEach(btn => {
    //         btn.onclick = function(e) {
    //             e.preventDefault(); 
                
    //             const scheduleName = this.closest('.details').querySelector('h4').textContent;
                
    //             if (confirm(`'${scheduleName}' 일정을 정말로 삭제하시겠습니까?`)) {
    //                 alert(`${scheduleName} 일정을 삭제합니다.`);
    //             } else {
    //                 alert("삭제가 취소되었습니다.");
    //             }
    //         };
    //     });
    // }
// 삭제 버튼이 아니면 무시
// ✅ 일정 삭제 (이벤트 위임 방식)
document.addEventListener("click", function (e) {

    // 삭제 버튼 아니면 무시
    if (!e.target.classList.contains("delete-btn")) return;

    e.preventDefault();

    const itemEl = e.target.closest(".timeline-item-content");
    const detailId = itemEl.dataset.itemId;

    if (!detailId) {
        console.error("❌ detail_id 없음");
        return;
    }

    const scheduleName =
        itemEl.querySelector(".header-info h4")?.textContent || "이 일정";

    if (!confirm(`'${scheduleName}' 일정을 정말 삭제하시겠습니까?`)) {
        return;
    }

    fetch("/schedule/delete-detail", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        credentials: "same-origin",
        body: JSON.stringify({
            detail_id: detailId   // ⭐ 서버 기준
        })
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            itemEl.remove(); // 🔥 화면 즉시 제거
        } else {
            alert(data.message || "삭제 실패");
        }
    })
    .catch(err => {
        console.error("삭제 오류:", err);
    });
});


    // ==========================================================
    // D-2. 전체 일정 목록 삭제 버튼 얼럿
    // ==========================================================
    if (listDelBtn) {
        listDelBtn.onclick = function(e) {
            e.preventDefault();
            
            if (confirm("이 전체 여행 일정을 정말로 삭제하고 목록으로 돌아가시겠습니까?")) {
                alert("전체 일정을 삭제하고 목록으로 이동합니다.");
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




 $(document).ready(function(){
    const tripDataElement = $('#trip-data')[0];
    let encodedMetaString = tripDataElement?.dataset?.tripMeta || '';
    let tripMeta = {};
    let decodedMetaString;

    if (encodedMetaString) {
        try {
            const stringWithSpaces = encodedMetaString.replace(/\+/g, ' '); 
            const decodedMetaString = decodeURIComponent(stringWithSpaces); 
           
            const trimmedMetaString = decodedMetaString.trim();

            if (trimmedMetaString && trimmedMetaString !== '{}') {
               tripMeta = JSON.parse(trimmedMetaString); 
            }
             
            if(Object.keys(tripMeta).length !== 0) {
                 console.log(" 트립정보 (로딩 성공):", tripMeta);
                 
                 $('#trip-title').text(tripMeta.title);
                 $('#trip-city').text(`- 여행지역 | ${tripMeta.city}`);
            } else {
                 throw new Error("파싱은 성공했으나 객체가 비어있음");
            }
            
        } catch (e) {
            console.error("오류: JSON 또는 URL 디코딩 실패. ", e);
            console.log("읽어온 원본 URL 인코딩 문자열:", encodedMetaString);
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
        
        const placeIds = tripMeta.selectedPlaceId;
        if (Array.isArray(placeIds)) {
            const $placeList = $('#place-list'); 
            
            placeIds.forEach(id => {
                // 각 ID를 <p> 태그로 만들어 목록 컨테이너에 추가
                $placeList.append(`<p>트립메타 ID: ${id}</p>`);
            });
        } else {
                    console.warn("selectedPlaceId는 배열이 아니거나 존재하지 않습니다.");
                }    
    
    }
        
        const urlParts = window.location.pathname.split('/');
        const tripIdFromUrl = urlParts[3];

    
    if (tripIdFromUrl) {
        console.log("현재 View 페이지의 Trip ID::", tripIdFromUrl);
    }

    });

    $(document).ready(function(){
    
    // URL에서 Trip ID 가져오기 (기존 로직 유지)
    const urlParts = window.location.pathname.split('/');
    const tripIdFromUrl = urlParts[3];

    if (tripIdFromUrl) {
        console.log("현재 View 페이지의 Trip ID::", tripIdFromUrl);
        
        // ----------------------------------------------------
        // 🚨 새로 추가하거나 수정해야 할 부분 🚨
        // 페이지 로드 완료 시, 즉시 최종 확정 요청을 보냅니다.
        // ----------------------------------------------------
        
        // 1. 최종 확정 데이터 가져오기 (⭐ 가장 중요한 함수)
        const finalScheduleData = getFinalScheduleData();
        const tripNo = tripIdFromUrl;

        if (finalScheduleData.length > 0) {
            sendFinalizeRequest(tripNo, finalScheduleData);
        }
    }
});

   function getFinalScheduleData() {
    const $dataElement = $('#final-schedule-data'); 
    let finalData = [];

    if ($dataElement.length) {
        let jsonData = $dataElement.data('schedule'); 
        
        // 데이터가 없는 경우를 미리 걸러냅니다.
        if (!jsonData) {
            console.log("INFO: 스케줄 데이터가 비어 있습니다.");
            return finalData;
        }

        // 만약 이미 객체라면 파싱할 필요가 없습니다.
        if (typeof jsonData === 'object') {
            return jsonData;
        }

        try {
            // 문자열인 경우에만 파싱 시도
            finalData = JSON.parse(jsonData);
            console.log("SUCCESS: 최종 데이터 로드 완료.");
        } catch (e) {
            // 파싱 에러 발생 시 데이터 내용 확인용 로그
            console.warn("CHECK: JSON 형식이 올바르지 않습니다. 데이터 내용:", jsonData);
        }
    }
    
    return finalData; 
}

document.getElementById("list-del-btn").addEventListener("click", function () {
    const tripNo = document.getElementById("trip_no").value;

    if (!tripNo) {
        alert("trip_no 없음 😱");
        return;
    }

    if (!confirm("이 여행을 삭제할까요? 되돌릴 수 없습니다 😢")) return;

    fetch("/schedule/delete-trip", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ trip_no: tripNo })
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            alert("여행이 삭제되었습니다 ✈️💨");
            location.href = "/schedule/list";
        } else {
            alert(data.message || "삭제 실패");
        }
    })
    .catch(() => {
        alert("서버 오류 발생 🤯");
    });
});




