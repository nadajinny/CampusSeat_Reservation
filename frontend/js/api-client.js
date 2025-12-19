(function (global) {
  const API_BASE_URL = (() => {
    // 같은 서버에서 서빙되는 경우 상대 경로 사용 (기본값: 빈 문자열)
    // 별도 서버에서 API를 호출해야 하는 경우 APP_API_BASE_URL 설정
    const base = global.APP_API_BASE_URL || "";
    return base.endsWith("/") ? base.slice(0, -1) : base;
  })();
  const STUDENT_ID_KEY = "studentId";
  const ACCESS_TOKEN_KEY = "accessToken";

  class ApiError extends Error {
    constructor(message, options = {}) {
      super(message || "요청 처리 중 오류가 발생했습니다.");
      this.name = "ApiError";
      this.code = options.code || null;
      this.status = options.status || null;
      this.payload = options.payload;
      this.raw = options.raw;
    }
  }

  function getAuth() {
    const studentId = sessionStorage.getItem(STUDENT_ID_KEY);
    const accessToken = sessionStorage.getItem(ACCESS_TOKEN_KEY);
    return {
      studentId: studentId || null,
      accessToken: accessToken || null,
    };
  }

  function setAuth({ studentId, accessToken }) {
    if (studentId) {
      sessionStorage.setItem(STUDENT_ID_KEY, String(studentId));
    }
    if (accessToken) {
      sessionStorage.setItem(ACCESS_TOKEN_KEY, accessToken);
    }
  }

  function clearAuth() {
    sessionStorage.removeItem(STUDENT_ID_KEY);
    sessionStorage.removeItem(ACCESS_TOKEN_KEY);
  }

  async function apiFetch(path, options = {}) {
    const url = `${API_BASE_URL}${path}`;
    const fetchOptions = { method: "GET", ...options };
    const headers = new Headers(fetchOptions.headers || {});

    if (fetchOptions.body && !(fetchOptions.body instanceof FormData)) {
      if (!headers.has("Content-Type")) {
        headers.set("Content-Type", "application/json");
      }
    }

    const auth = getAuth();
    if (auth.accessToken && !headers.has("Authorization")) {
      headers.set("Authorization", `Bearer ${auth.accessToken}`);
    }

    fetchOptions.headers = headers;

    const response = await fetch(url, fetchOptions);
    let data = null;
    const contentType = response.headers.get("content-type") || "";

    if (contentType.includes("application/json")) {
      data = await response.json();
    } else {
      data = await response.text();
    }

    if (!response.ok) {
      const message = data?.payload?.message || data?.message || data?.detail || "요청 처리 중 오류가 발생했습니다.";
      throw new ApiError(message, {
        status: response.status,
        code: data?.code || null,
        payload: data?.payload,
        raw: data,
      });
    }

    if (data?.is_success === false) {
      const message = data?.payload?.message || "요청 처리 중 오류가 발생했습니다.";
      throw new ApiError(message, {
        status: response.status,
        code: data?.code || null,
        payload: data?.payload,
        raw: data,
      });
    }

    return data;
  }

  async function login(studentId) {
    const normalizedId = String(studentId).trim();
    const body = JSON.stringify({ student_id: normalizedId });
    const data = await apiFetch("/api/auth/login", {
      method: "POST",
      body,
    });
    const payload = data?.payload;
    if (!payload) {
      throw new ApiError("로그인 응답을 확인할 수 없습니다.");
    }
    setAuth({ studentId: payload.student_id, accessToken: payload.access_token });
    return payload;
  }

  async function fetchMeetingRoomStatus(date) {
    const data = await apiFetch(`/api/status/meeting-rooms?date=${date}`);
    return data?.payload || null;
  }

  async function fetchSeatStatus(date) {
    const data = await apiFetch(`/api/status/seats?date=${date}`);
    return data?.payload || null;
  }

  async function createMeetingReservation(requestBody) {
    const data = await apiFetch("/api/reservations/meeting-rooms", {
      method: "POST",
      body: JSON.stringify(requestBody),
    });
    return data?.payload || null;
  }

  async function createSeatReservation(requestBody, { random = false } = {}) {
    const path = random ? "/api/reservations/seats/random" : "/api/reservations/seats";
    const data = await apiFetch(path, {
      method: "POST",
      body: JSON.stringify(requestBody),
    });
    return data?.payload || null;
  }

  async function fetchMyReservations(params = {}) {
    const searchParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== "") {
        searchParams.set(key, value);
      }
    });
    const query = searchParams.toString();
    const path = query ? `/api/reservations/me?${query}` : "/api/reservations/me";
    const data = await apiFetch(path);
    return data?.payload || null;
  }

  async function cancelReservation(reservationId) {
    const data = await apiFetch(`/api/reservations/me/${reservationId}`, {
      method: "DELETE",
    });
    return data?.payload || null;
  }

  global.ApiClient = {
    ApiError,
    apiFetch,
    login,
    fetchMeetingRoomStatus,
    fetchSeatStatus,
    createMeetingReservation,
    createSeatReservation,
    fetchMyReservations,
    cancelReservation,
    getAuth,
    setAuth,
    clearAuth,
  };
})(typeof window !== "undefined" ? window : globalThis);
