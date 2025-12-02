$(document).ready(function() {
  // 스와이퍼
  var swiper = new Swiper(".mySwiper", {
    slidesPerView: 4,
    spaceBetween: 15,
    pagination: {
      el: ".swiper-pagination",
      clickable: true,
    },
  });

});