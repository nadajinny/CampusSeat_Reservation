// js/app.js

document.addEventListener("DOMContentLoaded", () => {
  const studentId = sessionStorage.getItem("studentId");

  if (!studentId) {
    alert("로그인이 필요합니다.");
    window.location.href = "login.html";
    return;
  }
});

// js/app.js (아래 추가)
const userText = document.getElementById("studentIdText");
if (userText) {
  userText.textContent = studentId;
}

// js/app.js
const logoutBtn = document.getElementById("logoutBtn");
if (logoutBtn) {
  logoutBtn.addEventListener("click", () => {
    sessionStorage.clear();
    window.location.href = "login.html";
  });
}
