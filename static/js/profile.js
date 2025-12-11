document.addEventListener("DOMContentLoaded", function () {

    const styleNames = {
        spring_flower: "🌸 봄꽃",
        summer_sea: "☀️ 여름바다",
        autumn_leaf: "🍁 가을단풍",
        winter_snow: "❄️ 겨울눈",
        water_play: "🏊 물놀이",
        trekking: "🏃 운동/트레킹",
        food_tour: "🍜 맛집",
        healing: "🌿 힐링",
        night_view: "🌙 야경",
        activity: "🎢 액티비티"
    };

    const hiddenInput = document.getElementById("travel_style");
    const selectedValues = hiddenInput.value.split(",");
    const buttons = document.querySelectorAll(".style-btn");
    const max = 4;

    buttons.forEach(btn => {
        const value = btn.getAttribute("data-value");

        // 버튼 라벨 한글로 변경
        btn.innerText = styleNames[value];

        // 기존 선택 반영
        if (selectedValues.includes(value)) {
            btn.classList.add("selected");
        }

        btn.addEventListener("click", function () {
            btn.classList.toggle("selected");

            let selected = [...document.querySelectorAll(".style-btn.selected")]
                .map(e => e.dataset.value);

            if (selected.length > max) {
                btn.classList.remove("selected");
                alert("최대 4개까지 선택할 수 있어요!");
                return;
            }

            hiddenInput.value = selected.join(",");
        });
    });
});
