// ⭐ 프로필 드롭다운 열고 닫기 전용 JS ⭐
document.addEventListener("DOMContentLoaded", function () {
    const toggle = document.getElementById("profileToggle");
    const menu = document.getElementById("profileMenu");

    if (toggle) {
        toggle.addEventListener("click", function (e) {
            e.stopPropagation();
            menu.style.display = (menu.style.display === "block") ? "none" : "block";
        });
    }

    // 화면 밖 클릭 시 자동 닫힘
    document.addEventListener("click", function () {
        if (menu) menu.style.display = "none";
    });
});


// 🌙 다크모드 토글 기능
document.addEventListener("DOMContentLoaded", function () {
    const toggleThemeBtn = document.getElementById("toggleTheme");

    if (!toggleThemeBtn) return;

    // 기존 설정 적용
    if (localStorage.getItem("theme") === "dark") {
        document.body.classList.add("dark-mode");
    }

    toggleThemeBtn.addEventListener("click", function (e) {
        e.preventDefault();

        document.body.classList.toggle("dark-mode");

        // 저장
        if (document.body.classList.contains("dark-mode")) {
            localStorage.setItem("theme", "dark");
        } else {
            localStorage.setItem("theme", "light");
        }
    });
});
