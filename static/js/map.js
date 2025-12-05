        
// 동적으로 URL을 생성하고 <script> 태그를 문서에 삽입합니다.
const script = document.createElement('script');
script.type = 'text/javascript';
script.src = `//dapi.kakao.com/v2/maps/sdk.js?appkey=${MAP_API_KEY}&autoload=false`;

var map = null;

script.onload = 
function() {
	kakao.maps.load( function(){
		initializeMap(MapX, MapY);
	});
};

document.head.appendChild(script);

function initializeMap(mapX, mapY) {
	const defaultLat = 33.450701; // 기본 위도
	const defaultLng = 126.570667; // 기본 경도

	const Lat = parseFloat(mapY) || defaultLat;
	const Lng = parseFloat(mapX) || defaultLng;

	const centerLatLng = new kakao.maps.LatLng(Lat, Lng);
	//지도를 담을 영역의 DOM 레퍼런스
	var container = document.getElementById('map');
	// 만약 #map 요소가 없다면 함수를 종료합니다.
  if (!container) return;
	
		container.style.width = "100%";
		container.style.height = "650px";

	var options = { //지도를 생성할 때 필요한 기본 옵션
		center: centerLatLng,
		level: 3 //지도의 레벨(확대, 축소 정도)
	};
	map = new kakao.maps.Map(container, options); // 지도 생성 및 객체 리턴
	
	map.relayout();

	var marker = new kakao.maps.Marker({
		position: centerLatLng
	});
	marker.setMap(map);
}