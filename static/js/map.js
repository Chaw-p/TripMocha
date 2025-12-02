const MAP_API_KEY = window.AppConfig.MAP_API_KEY;
        
// 동적으로 URL을 생성하고 <script> 태그를 문서에 삽입합니다.
const script = document.createElement('script');
script.type = 'text/javascript';
script.src = `//dapi.kakao.com/v2/maps/sdk.js?appkey=${MAP_API_KEY}&autoload=false`;

// (선택 사항) 서비스 로딩 완료 후 지도를 띄우고 싶다면 &autoload=false 추가 후 아래처럼 로드합니다.
// script.onload = () => {
//     kakao.maps.load(() => {
//         // 지도 초기화 코드
//     });
// };

document.head.appendChild(script);

var container = document.getElementById('map'); //지도를 담을 영역의 DOM 레퍼런스
var options = { //지도를 생성할 때 필요한 기본 옵션
	center: new kakao.maps.LatLng(33.450701, 126.570667), //지도의 중심좌표.
	level: 3 //지도의 레벨(확대, 축소 정도)
};

var map = new kakao.maps.Map(container, options); //지도 생성 및 객체 리턴

