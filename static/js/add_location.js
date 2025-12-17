var $travel_list; 
var loading;

// travel 내의 비동기함수
const page = {
  _page: 1, // 현재 페이지 번호
  _scrollchk: false, // 로딩 중 플래그 (코드에는 전역 변수 _scrollchk로 사용됨)
  list: {
    search: async function() {
      const locQuery = document.getElementById("locQuery").value;
      const locType = $('#locType .option_item.selected').data('value');
      const paramsToSend = { 
        page: page._page,
        query: locQuery,
        type: locType
      };

      const searchParams = new URLSearchParams(paramsToSend).toString();

      try {
        // 로딩
        page._scrollchk = true; 
        $("#waitMsg").show();
        // 조회
        const response = await fetch(`/info/tourapi?${searchParams}`, { method: "GET" });
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        // data
        if (data.items && data.items.length > 0) {
          $travel_list.find('.no-result').hide();
          data.items.forEach(function(item) {
            // 서버에서 받은 items 배열
            var html = `
              <li>
                <a href="/info/${item.id}">
                  <img src="${item.image}">
                </a>
                <div class="list_cont">
                  <h3 class="title" id="item-title">
                      <a href="/info/${item.id}">${item.title}</a>
                  </h3>
                  <p class="loc" id="addr1">${item.addr1}</p>
                  <input type="hidden" class="loc" id="item-mapX" value=${item.mapX}>
                  <input type="hidden" class="loc" id="item-mapY" value=${item.mapY}>
                  <p class="hash">
                  </p>
                </div>
              </li>
              `;
            $("#sentinel").before(html);
          });
          page._page += 1;
        } else {
          // 데이터가 없을 경우 (검색 결과가 없거나, 마지막 페이지): 옵저버를 해제합니다.
          const sentinel = document.getElementById('sentinel');
          if (sentinel) {
              io.unobserve(sentinel); 
              console.log("마지막 페이지 도달. IntersectionObserver 해제.");
          }
        }
        // data
        return data;
      } catch (error) {
        console.error("Fetch 또는 JSON 파싱 중 오류 발생:", error);
        throw error;
      }finally {
        page._scrollchk = false;
        $("#waitMsg").hide();
      }
      
    }
  }
};

// travel 내의 search 함수
function DoSearch2(event) {
  const no_result_Html = `
    <div class="no-result">
        <p>
            <span class="material-symbols-outlined">search</span>
        </p>
        <p>
            검색 결과가 없습니다.
        </p>
    </div>
    <li id="sentinel" style="height: 1px; margin: 0; padding: 0;"></li>
`;
  event.preventDefault();

  page._page = 1; 
    // 기존 목록 초기화
  if ($travel_list) {
      $travel_list.get(0).scrollTo({
        top: 0,
        behavior: 'smooth' // 👈 부드러운 스크롤 효과 적용
    });
      $travel_list.empty();
      $travel_list.append(no_result_Html);
  }

   // 무한 스크롤 감지
  const sentinel = document.getElementById('sentinel');
  if (sentinel) {
    // 기존 관찰 중지 후,
    io.unobserve(sentinel); 
    // 새롭게 관찰 시작.
    io.observe(sentinel);
  }

  page.list.search();
  
  return false;
}
const io = new IntersectionObserver((entries, observer) => {
	entries.forEach(entry => {
	  if (!entry.isIntersecting) return; 
	  if (page._scrollchk) return;

    page.list.search();
	});
});

function SelectedLiData() {
  const $selectedLi = $('#schedule_travel_list').find('li.selected');
  if ($selectedLi.length === 0) {
        console.log("선택된 여행지가 없습니다.");
        return null;
  }

  const title = $selectedLi.find('#item-title a').text().trim(); 
  const addr1 = $selectedLi.find('#item-addr1').text().trim();    
  const mapX = $selectedLi.find('#item-mapX').val();
  const mapY = $selectedLi.find('#item-mapY').val();

  const selectedData = {
        title: title,
        addr1: addr1,
        mapX: mapX,
        mapY: mapY
  };

  console.log("--- 선택된 여행지 정보 ---");
  console.log(selectedData);
  console.log("------------------------");
  
  return selectedData;
}

$(document).ready(function() {
  $travel_list = $('#schedule_travel_list');
  loading = $('#waitMsg');
});

$(document).on("click", "#schedule_travel_list > li", function(){
  $("#schedule_travel_list > li").removeClass("selected")
  $(this).addClass("selected")
})
// 드롭다운 리스트를 골랐을때 li값으로 변경
$(document).on("click", ".options_dropdown  li", function(){
  $(this).siblings().removeClass('selected');
  $(this).addClass('selected');
  $(this).closest('.options_dropdown').find('.selected_option').html(
    $(this).text().trim() + ' <span class="material-symbols-outlined">arrow_drop_down</span>'
  );
  $(this).closest('.options_dropdown').removeClass('active');
});
// .selected_option을 클릭했을 때, active라는 클래스 추가
$(document).on("click", ".selected_option", function(){
  $(this).closest('.options_dropdown').toggleClass('active');
});

// // place_id 값 추가 함수
// async function InsertPlaceId() {
//   const selectedData = SelectedLiData();

//   // 데이터가 없으면 중단 //이후 수정
//   if (!selectedData) {
//       alert("먼저 여행지를 선택해주세요!");
//       return;
//   }
//   const url = `/info/location/${tripNo}`;

// }