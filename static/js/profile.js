document.addEventListener("DOMContentLoaded", function () {

    /* ===============================
       0️⃣ 상태 변수
    =============================== */
    let unlocked = false;        // 현재 비밀번호 인증 여부
    let lastResult = null;       // 현재 비밀번호 toast 중복 방지
    let lastPwMatch = null;      // 새 비밀번호 비교 toast 중복 방지

    const pwInput = document.getElementById("current_pw");
    const lockTargets = document.querySelectorAll(".lock-target");

    const newPwInput = document.querySelector('input[name="new_password"]');
    const newPwCheckInput = document.querySelector('input[name="new_password_confirm"]');

    /* ===============================
       1️⃣ 잠금 / 해제 함수
    =============================== */
    function lockAll() {
        lockTargets.forEach(el => {
            if (el.tagName === "INPUT") {
                el.disabled = true;
                el.readOnly = true;
            } else {
                el.disabled = true;
            }
        });
    }

    function unlockAll() {
        lockTargets.forEach(el => {
            if (el.tagName === "INPUT") {
                el.disabled = false;
                el.readOnly = false;
            } else {
                el.disabled = false;
            }
        });
    }

    // 최초 진입 시 무조건 잠금
    lockAll();

    /* ===============================
       2️⃣ 새 비밀번호 / 확인 비교
    =============================== */
    function checkPasswordMatch() {

        // 🔒 잠겨 있으면 비교 안 함
        if (!unlocked) return;

        const pw = newPwInput.value;
        const pwCheck = newPwCheckInput.value;

        if (!pw || !pwCheck) {
            lastPwMatch = null;
            return;
        }

        const isMatch = pw === pwCheck;

        if (isMatch === lastPwMatch) return;
        lastPwMatch = isMatch;

        if (isMatch) {
            showToast("새 비밀번호가 서로 똑같습니다 👍");
        } else {
            showToast("새 비밀번호가 서로 다릅니다 ❌");
        }
    }

    newPwInput.addEventListener("input", checkPasswordMatch);
    newPwCheckInput.addEventListener("input", checkPasswordMatch);

    /* ===============================
       3️⃣ 현재 비밀번호 자동 검사
    =============================== */
    pwInput.addEventListener("input", function () {
        const pw = pwInput.value.trim();

        if (pw.length < 4) {
            unlocked = false;
            lastResult = null;
            lastPwMatch = null;
            lockAll();
            return;
        }

        fetch("/api/check_current_password", {
            method: "POST",
            headers: {
                "Content-Type": "application/x-www-form-urlencoded",
            },
            body: `current_password=${encodeURIComponent(pw)}`
        })
        .then(res => res.json())
        .then(data => {

            if (data.success === lastResult) return;
            lastResult = data.success;

            if (data.success) {
                unlocked = true;
                lastPwMatch = null;
                unlockAll();
                showToast("현재 비밀번호 확인 완료! 수정할 수 있어요 ✅");
            } else {
                unlocked = false;
                lockAll();
                showToast("현재 비밀번호가 틀렸어요 ❌");
            }
        });
    });

    /* ===============================
       4️⃣ 여행 스타일 버튼 로직
    =============================== */
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
    const selectedValues = hiddenInput.value
        ? hiddenInput.value.split(",")
        : [];

    const buttons = document.querySelectorAll(".style-btn");
    const max = 4;

    buttons.forEach(btn => {
        const value = btn.dataset.value;
        btn.innerText = styleNames[value];

        if (selectedValues.includes(value)) {
            btn.classList.add("selected");
        }

        btn.addEventListener("click", function () {

            if (!unlocked) {
                showToast("비밀번호 확인 후 수정할 수 있어요 🔒");
                return;
            }

            btn.classList.toggle("selected");

            let selected = [...document.querySelectorAll(".style-btn.selected")]
                .map(e => e.dataset.value);

            if (selected.length > max) {
                btn.classList.remove("selected");
                showToast("여행 스타일은 최대 4개까지 선택 가능해요!");
                return;
            }

            hiddenInput.value = selected.join(",");
        });
    });

});

/* ===============================
   Toast
=============================== */
function showToast(message, duration = 2000) {
    const toast = document.getElementById("toast");
    if (!toast) return;

    toast.textContent = message;
    toast.classList.add("show");

    setTimeout(() => {
        toast.classList.remove("show");
    }, duration);
}
