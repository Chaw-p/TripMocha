// ================================
// 토스트 메시지 표시 함수
// ================================
function showToast(message) {
    const toast = document.getElementById("toast");

    toast.textContent = message;
    toast.classList.remove("hidden");
    toast.classList.add("show");

    setTimeout(() => {
        toast.classList.remove("show");
        toast.classList.add("hidden");
    }, 2500);
}

// ================================
// 서버에서 전달된 에러 메시지 자동 표시
// ================================
document.addEventListener("DOMContentLoaded", () => {
    const toastMessage = document.body.dataset.toast;
    if (toastMessage) {
        showToast(toastMessage);
    }
});
