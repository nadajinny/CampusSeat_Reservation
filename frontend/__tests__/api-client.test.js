const createSessionStorage = () => {
  let store = {};
  return {
    getItem: (key) => (Object.prototype.hasOwnProperty.call(store, key) ? store[key] : null),
    setItem: (key, value) => {
      store[key] = String(value);
    },
    removeItem: (key) => {
      delete store[key];
    },
    clear: () => {
      store = {};
    },
  };
};

if (!global.Headers) {
  class HeadersShim {
    constructor(init = {}) {
      this.map = new Map();
      if (init instanceof HeadersShim) {
        init.forEach((value, key) => this.set(key, value));
      } else if (Array.isArray(init)) {
        init.forEach(([key, value]) => this.set(key, value));
      } else if (init && typeof init === "object") {
        Object.entries(init).forEach(([key, value]) => this.set(key, value));
      }
    }

    set(key, value) {
      this.map.set(String(key).toLowerCase(), String(value));
    }

    get(key) {
      return this.map.get(String(key).toLowerCase()) || null;
    }

    has(key) {
      return this.map.has(String(key).toLowerCase());
    }

    forEach(callback) {
      this.map.forEach((value, key) => callback(value, key));
    }
  }

  global.Headers = HeadersShim;
}

if (!global.FormData) {
  global.FormData = class FormData {};
}

const buildJsonResponse = (body, { ok = true, status = 200 } = {}) => ({
  ok,
  status,
  headers: new Headers({ "content-type": "application/json" }),
  json: async () => body,
  text: async () => JSON.stringify(body),
});

const buildTextResponse = (text, { ok = true, status = 200 } = {}) => ({
  ok,
  status,
  headers: new Headers({ "content-type": "text/plain" }),
  json: async () => ({ message: text }),
  text: async () => text,
});

const loadApiClient = () => {
  jest.resetModules();
  require("../js/api-client");
  return global.ApiClient;
};

beforeEach(() => {
  global.APP_API_BASE_URL = "http://example.com/";
  global.sessionStorage = createSessionStorage();
  global.fetch = jest.fn();
});

afterEach(() => {
  delete global.ApiClient;
  delete global.APP_API_BASE_URL;
});

describe("ApiClient 인증 상태 관리", () => {
  test("인증 정보가 없으면 null을 반환한다", () => {
    const ApiClient = loadApiClient();
    expect(ApiClient.getAuth()).toEqual({ studentId: null, accessToken: null });
  });

  test("인증 정보를 저장하고 삭제한다", () => {
    const ApiClient = loadApiClient();
    ApiClient.setAuth({ studentId: "202300001", accessToken: "token-123" });
    expect(ApiClient.getAuth()).toEqual({ studentId: "202300001", accessToken: "token-123" });

    ApiClient.clearAuth();
    expect(ApiClient.getAuth()).toEqual({ studentId: null, accessToken: null });
  });
});

describe("ApiClient apiFetch", () => {
  test("JSON body 요청에 Content-Type과 Authorization을 설정한다", async () => {
    const ApiClient = loadApiClient();
    global.sessionStorage.setItem("accessToken", "access-123");
    global.fetch.mockResolvedValue(buildJsonResponse({ payload: { ok: true } }));

    await ApiClient.apiFetch("/api/test", {
      method: "POST",
      body: JSON.stringify({ value: 1 }),
    });

    const [url, options] = global.fetch.mock.calls[0];
    expect(url).toBe("http://example.com/api/test");
    expect(options.headers.get("Content-Type")).toBe("application/json");
    expect(options.headers.get("Authorization")).toBe("Bearer access-123");
  });

  test("JSON이 아닌 응답은 텍스트로 반환한다", async () => {
    const ApiClient = loadApiClient();
    global.fetch.mockResolvedValue(buildTextResponse("pong"));

    const result = await ApiClient.apiFetch("/api/ping");

    expect(result).toBe("pong");
  });

  test("응답이 실패하면 ApiError를 던진다", async () => {
    const ApiClient = loadApiClient();
    global.fetch.mockResolvedValue(
      buildJsonResponse(
        { code: "BAD_REQUEST", payload: { message: "요청 실패" } },
        { ok: false, status: 400 }
      )
    );

    await expect(ApiClient.apiFetch("/api/fail")).rejects.toMatchObject({
      name: "ApiError",
      message: "요청 실패",
      status: 400,
      code: "BAD_REQUEST",
    });
  });

  test("is_success가 false면 ApiError를 던진다", async () => {
    const ApiClient = loadApiClient();
    global.fetch.mockResolvedValue(
      buildJsonResponse({ is_success: false, code: "FAIL", payload: { message: "처리 실패" } })
    );

    await expect(ApiClient.apiFetch("/api/fail")).rejects.toMatchObject({
      name: "ApiError",
      message: "처리 실패",
      code: "FAIL",
    });
  });
});

describe("ApiClient login", () => {
  test("학번을 정규화하고 인증 정보를 저장한다", async () => {
    const ApiClient = loadApiClient();
    global.fetch.mockResolvedValue(
      buildJsonResponse({ payload: { student_id: "202300001", access_token: "token-999" } })
    );

    const payload = await ApiClient.login(" 202300001 ");
    const [url, options] = global.fetch.mock.calls[0];

    expect(url).toBe("http://example.com/api/auth/login");
    expect(JSON.parse(options.body)).toEqual({ student_id: "202300001" });
    expect(payload).toEqual({ student_id: "202300001", access_token: "token-999" });
    expect(ApiClient.getAuth()).toEqual({ studentId: "202300001", accessToken: "token-999" });
  });

  test("payload가 없으면 에러를 던진다", async () => {
    const ApiClient = loadApiClient();
    global.fetch.mockResolvedValue(buildJsonResponse({}));

    await expect(ApiClient.login("202300001")).rejects.toMatchObject({
      name: "ApiError",
      message: "로그인 응답을 확인할 수 없습니다.",
    });
  });
});

describe("ApiClient 예약 요청", () => {
  test("좌석 랜덤 예약은 전용 경로를 사용한다", async () => {
    const ApiClient = loadApiClient();
    global.fetch.mockResolvedValue(buildJsonResponse({ payload: { id: "R-1" } }));

    await ApiClient.createSeatReservation({ seat_id: "SEAT-1" });
    expect(global.fetch.mock.calls[0][0]).toBe("http://example.com/api/reservations/seats");

    global.fetch.mockClear();
    global.fetch.mockResolvedValue(buildJsonResponse({ payload: { id: "R-2" } }));

    await ApiClient.createSeatReservation({ seat_id: "SEAT-1" }, { random: true });
    expect(global.fetch.mock.calls[0][0]).toBe("http://example.com/api/reservations/seats/random");
  });

  test("예약 조회 파라미터는 빈 값 없이 직렬화한다", async () => {
    const ApiClient = loadApiClient();
    global.fetch.mockResolvedValue(buildJsonResponse({ payload: [] }));

    await ApiClient.fetchMyReservations({ date: "2030-01-08", status: "", type: "MEETING" });

    expect(global.fetch.mock.calls[0][0]).toBe(
      "http://example.com/api/reservations/me?date=2030-01-08&type=MEETING"
    );
  });

  test("조회 파라미터가 없으면 기본 경로를 사용한다", async () => {
    const ApiClient = loadApiClient();
    global.fetch.mockResolvedValue(buildJsonResponse({ payload: [] }));

    await ApiClient.fetchMyReservations();

    expect(global.fetch.mock.calls[0][0]).toBe("http://example.com/api/reservations/me");
  });

  test("회의실 예약은 전용 경로로 전송한다", async () => {
    const ApiClient = loadApiClient();
    global.fetch.mockResolvedValue(buildJsonResponse({ payload: { id: "M-1" } }));

    await ApiClient.createMeetingReservation({ room_id: 1, date: "2030-01-08" });

    const [url, options] = global.fetch.mock.calls[0];
    expect(url).toBe("http://example.com/api/reservations/meeting-rooms");
    expect(options.method).toBe("POST");
    expect(JSON.parse(options.body)).toEqual({ room_id: 1, date: "2030-01-08" });
  });

  test("예약 취소는 DELETE 메서드를 사용한다", async () => {
    const ApiClient = loadApiClient();
    global.fetch.mockResolvedValue(buildJsonResponse({ payload: { id: "R-1" } }));

    await ApiClient.cancelReservation("R-1");

    const [url, options] = global.fetch.mock.calls[0];
    expect(url).toBe("http://example.com/api/reservations/me/R-1");
    expect(options.method).toBe("DELETE");
  });
});

describe("ApiClient 상태 조회", () => {
  test("회의실 상태 조회는 날짜 파라미터를 포함한다", async () => {
    const ApiClient = loadApiClient();
    global.fetch.mockResolvedValue(buildJsonResponse({ payload: { rooms: [] } }));

    const result = await ApiClient.fetchMeetingRoomStatus("2030-01-08");

    expect(global.fetch.mock.calls[0][0]).toBe(
      "http://example.com/api/status/meeting-rooms?date=2030-01-08"
    );
    expect(result).toEqual({ rooms: [] });
  });

  test("좌석 상태 조회는 날짜 파라미터를 포함한다", async () => {
    const ApiClient = loadApiClient();
    global.fetch.mockResolvedValue(buildJsonResponse({ payload: { seats: [] } }));

    const result = await ApiClient.fetchSeatStatus("2030-01-08");

    expect(global.fetch.mock.calls[0][0]).toBe(
      "http://example.com/api/status/seats?date=2030-01-08"
    );
    expect(result).toEqual({ seats: [] });
  });
});
