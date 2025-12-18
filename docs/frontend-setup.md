# ⚙️ 프런트엔드 개발 환경 & 실행

정적 서버와 Jest 환경을 갖추기 위한 필수 설정을 정리했습니다.

| 구분 | 내용 |
| --- | --- |
| 정적 서버 | `python3 -m http.server 5500` (항상 `frontend/` 루트에서 실행) |
| API 기본 URL | `http://127.0.0.1:8000` (필요 시 `window.APP_API_BASE_URL`로 오버라이드) |
| 세션 유지 | `sessionStorage`에 `studentId`, `accessToken`을 저장. 동일 host:port(예: `127.0.0.1:5500`)에서 페이지를 열어야 토큰 공유가 가능합니다. |
| 의존성 | `npm install` (Jest 테스트 실행 시 필요) |
| 테스트 | `npm test` → `__tests__/reservation-engine.test.js` 실행 |

## 실행 순서 예시

```bash
cd frontend
npm install          # 처음 한 번
python3 -m http.server 5500
# 브라우저에서 http://127.0.0.1:5500/login.html 진입
```
