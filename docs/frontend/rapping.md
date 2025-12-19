# 📦 프런트엔드 응답 처리 가이드

프런트는 **`frontend/js/api-client.js`**를 통해 응답을 일관되게 처리합니다.  
이 문서는 **어디서 호출하고 어떤 규칙으로 처리하는지**만 정리합니다.

---

## 1. 응답 구조

```json
{
  "is_success": true,
  "code": null,
  "payload": {}
}
```

### 처리 규칙

- `response.ok === false` → `ApiError` 발생
- `is_success === false` → `ApiError` 발생
- UI는 항상 `payload`만 사용

---

## 2. ApiClient 흐름

`apiFetch()`는 아래 처리를 자동화합니다.

1. `Content-Type` 자동 설정 (`application/json`)
2. `Authorization` 헤더 자동 부착
3. JSON 또는 Text 응답 파싱
4. 에러 응답을 `ApiError`로 변환

---

## 3. 사용 예시

```js
try {
  const payload = await ApiClient.fetchMeetingRoomStatus(date);
  renderMeetingTimeSlots(payload);
} catch (error) {
  showError(error.message);
}
```

---

## 4. ApiError 활용

`ApiError`는 다음 정보를 제공합니다.

- `message`: 사용자 메시지
- `status`: HTTP 상태 코드
- `code`: 백엔드 에러 코드 문자열
- `payload`: 원본 payload
- `raw`: 원본 응답 객체

필요 시 에러 코드에 따라 UI 메시지를 세분화할 수 있습니다.
