
var $travel_list; 
var loading;

const currentPath = window.location.pathname;
const urlParams = new URLSearchParams(window.location.search);
const params = {
    type: urlParams.get('type') || 'AC',
    area: urlParams.get('area'),
    cat: urlParams.get('cat')
};
urlParams.forEach((value, key) => {
  // page 파라미터를 제외한 모든 파라미터를 params 객체에 추가합니다.
  if (key !== 'page') {
      params[key] = value;
  }
});
// 페이지 상태 관리 객체 (무한 스크롤에 필수)
const page = {
    _page: 1, // 현재 페이지 번호
    _scrollchk: false, // 로딩 중 플래그 (코드에는 전역 변수 _scrollchk로 사용됨)
    list: {
      // search 함수를 포함할 객체. 여기에 AJAX 코드를 정의해야 합니다.
      search: function() {

        const paramsToSend = { 
        ...params, // 모든 기존 필터 (type, area, cat, query 등)

        page: page._page
        };

        $.ajax({
          url: "/info/tourapi",
          data:  paramsToSend,
          method: "GET",
          dataType: "json",
          success: function(response) {
            // 로딩 숨김
            loading.hide(); 
            //디버그//
            // console.log("AJAX Success. Page:", page._page);
            // console.log("Received items count:", response.items ? response.items.length : 0);

            if (response.items && response.items.length > 0) {

              response.items.forEach(function(item) {
                // 서버에서 받은 items 배열
                const typeUrl = `${currentPath}?type=${item.typecode1}`;
                const areaUrl = typeUrl + `&area=${item.areacode}`;
                const catUrl = typeUrl + `&cat=${item.cat3}`;
                var html = `
                  <li>
                    <a href="/info/${item.id}">
                        <img src="${item.image}">
                    </a>
                    <div class="list_cont">
                        <h3 class="title">
                            <a href="/info/${item.id}">${item.title}</a>
                        </h3>
                        <p class="loc">${item.addr1}</p>
                        <p class="hash">
                            <a href="${typeUrl}" 
                              ${item.typecode1 === params.type ? 'class="selected_hash"' : ''}>
                              <span>#${item.type}</span>
                            </a>
                            <a href="${areaUrl}" 
                              ${item.areacode === params.area ? 'class="selected_hash"' : ''}>
                              <span>#${item.area}</span>
                            </a>
                            ${item.cat3 && item.cat3_name ? `
                              <a href="${catUrl}"
                                  ${item.cat3 === params.cat ? 'class="selected_hash"' : ''}>
                                  <span>#${item.cat3_name}</span>
                              </a>` : ''}
                        </p>
                    </div>
                  </li>
                  `;
                $travel_list.append(html);
              });
              //디버그//
              // console.log("After append - LI count:", $travel_list.children('li').length);
              // console.log("$travel_list element:", $travel_list[0]);
            } else {
              $travel_list.append('<li>검색 결과가 없습니다.</li>');
                
              // 💡 최종 페이지 처리: 옵저버 해제
              const sentinel = document.getElementById('sentinel');
              if (sentinel) {
                  io.unobserve(sentinel); 
                  console.log("마지막 페이지 도달. IntersectionObserver 해제.");
              }
            }
          },
          error: function(xhr, status, error) {
            loading.hide();
            $travel_list.append('<li>데이터를 불러오는 중 오류가 발생했습니다.</li>');
            console.error("AJAX Error:", status, error);
          },
          beforeSend: function () {
            page._scrollchk = true; 
            //데이터가 로드 중임을 나타내는 flag입니다.
            // document.getElementById('travel_list').appendChild(skeleton.show()); // 바로 게시글을 추가하기 때문에 사용하지 않는다.
            //skeleton을 그리는 함수를 이용해 DOM에 추가해줍니다.
            $("#waitMsg").show();
            //loading animation을 가진 요소를 보여줍니다.
          },
          complete: function () {
            page._scrollchk = false;
            //데이터가 로드 중임을 나타내는 flag입니다.
            $("#waitMsg").hide();
            // skeleton.hide();
            //loading animation 요소와 skeleton을 지우는 함수를 이용해 DOM에서 지워줍니다.
          }
        });
      }
    }
};

//https://velog.io/@eunoia/%EB%AC%B4%ED%95%9C-%EC%8A%A4%ED%81%AC%EB%A1%A4Infinite-scroll-%EA%B5%AC%ED%98%84%ED%95%98%EA%B8%B0
const io = new IntersectionObserver((entries, observer) => {
	entries.forEach(entry => {
		//entry가 interscting 중이 아니라면 함수를 실행하지 않습니다.
	  if (!entry.isIntersecting) return; 
		//현재 page가 불러오는 중임을 나타내는 flag를 통해 불러오는 중이면 함수를 실행하지 않습니다.
	  if (page._scrollchk) return;

		//불러올 페이지를 추가합니다.
    page._page += 1;

    page.list.search();
		//페이지를 불러오는 함수를 호출합니다.
	});
});

$(document).ready(function() {
  $travel_list = $('#travel_list');
  loading = $('#waitMsg');

  // 무한 스크롤 감지
  const sentinel = document.getElementById('sentinel');
  if (sentinel) {
      io.observe(sentinel);
  }

});
