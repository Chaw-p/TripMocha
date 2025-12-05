var scrollThreshold = 50; 

$(document).ready(function() {

  // header
  var currentPath = window.location.pathname;
  var isIndexPage = currentPath === '/' || currentPath.includes('/index');

  console.log("currentPath:" + currentPath);

  // 스와이퍼
  var swiper = new Swiper(".mySwiper", {
    slidesPerView: 4,
    spaceBetween: 15,
    pagination: {
      el: ".swiper-pagination",
      clickable: true,
    },
  });

  Scroll(isIndexPage);

});

function Scroll(isIndexPage){
  // 스크롤 이벤트를 감지합니다.
    $(window).on('scroll', function() {
        // 1. 스크롤 위치를 가져옵니다.
        // 현재 뷰포트의 상단이 문서 상단에서 얼마나 떨어져 있는지 (픽셀 단위)
        const scrollPosition = $(window).scrollTop();
        
        // 2. 클래스를 추가할 기준 스크롤 값 (Threshold)을 설정합니다.
        // 예를 들어, 50px 이상 스크롤 했을 때 border가 나타나게 설정합니다.
        if(isIndexPage) {
          scrollThreshold = 50;
        }else
        {
          scrollThreshold = -50;
        }
        // 3. 조건문으로 클래스를 토글합니다.
        if (scrollPosition > scrollThreshold) {
            // 스크롤이 기준 값보다 크면 클래스를 추가
            $('#header').addClass('header-scrolled');
            if(scrollPosition > (scrollThreshold*2 + 20)){
              $('#nav_search_wrap').addClass('search-scrolled');
            }else{
              $('#nav_search_wrap').removeClass('search-scrolled');
            }
        } else {
            // 스크롤이 기준 값보다 작으면 클래스를 제거
            $('#header').removeClass('header-scrolled');
            $('#nav_search_wrap').removeClass('search-scrolled');
        }
    });

    // 페이지 로드 시 스크롤이 이미 내려가 있을 경우를 위해
    // 로드 직후 한 번 호출하여 초기 상태를 확인.
    $(window).trigger('scroll');
}


  




