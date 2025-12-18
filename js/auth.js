// js/auth.js

document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("login-form");
  if (!form) return;

  form.addEventListener("submit", (e) => {
    e.preventDefault();

    const studentId = document.getElementById("studentId").value.trim();
    const password = document.getElementById("password").value.trim();

    // 1. 학번 형식 검사 (9자리 숫자)
    const isNineDigitNumber = /^\d{9}$/.test(studentId);

    // 2. 하드코딩된 잘못된 학번
    const invalidIds = ["202099999", "202288888"];

    if (!isNineDigitNumber) {
      alert("학번은 9자리 숫자여야 합니다.");
      return;
    }

    if (invalidIds.includes(studentId)) {
      alert("유효하지 않은 학번입니다.");
      return;
    }

    // 3. 로그인 성공 처리
    sessionStorage.setItem("studentId", studentId);

    // 비밀번호는 테스트 대상 아니므로 저장 안 해도 됨
    alert("로그인 성공");
    window.location.href = "dashboard.html";
  });
});
