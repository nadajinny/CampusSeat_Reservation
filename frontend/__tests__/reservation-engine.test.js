const { ReservationEngine } = require("../js/reservation-engine");

const USER_ID = "202300001";
const FUTURE_DATE = "2030-01-08";
const ANOTHER_DATE = "2030-01-09";

const slot = (id, startHour, endHour) => ({
  id,
  startMinutes: startHour * 60,
  endMinutes: endHour * 60,
  label: `${String(startHour).padStart(2, "0")}:00 ~ ${String(endHour).padStart(2, "0")}:00`,
});

const SLOT_9_10 = slot("09-10", 9, 10);
const SLOT_10_11 = slot("10-11", 10, 11);
const SLOT_11_12 = slot("11-12", 11, 12);
const SLOT_09_11 = slot("09-11", 9, 11);
const SLOT_11_13 = slot("11-13", 11, 13);
const SLOT_13_15 = slot("13-15", 13, 15); // 2 hours for seats
const SLOT_14_16 = slot("14-16", 14, 16);
const SLOT_15_17 = slot("15-17", 15, 17);
const SLOT_16_18 = slot("16-18", 16, 18);
const SLOT_17_19 = slot("17-19", 17, 19);

const meetingReservation = ({ date, slot: slotObj, roomId = "MR-1", studentId = USER_ID }) => ({
  id: `M-${Math.random().toString(36).slice(2)}`,
  studentId,
  spaceType: "MEETING",
  date,
  roomId,
  roomName: roomId,
  timeSlots: [slotObj],
});

const seatReservation = ({ date, slots, seatId = "SEAT-1", studentId = USER_ID }) => ({
  id: `R-${Math.random().toString(36).slice(2)}`,
  studentId,
  spaceType: "READING",
  date,
  seatId,
  timeSlots: slots,
});

describe("회의실 예약 검증", () => {
  const baseRequest = {
    date: FUTURE_DATE,
    slot: SLOT_9_10,
    roomId: "MR-1",
    participants: ["123456789", "987654321", "111222333"],
  };

  test("인증되지 않은 요청은 거부한다", () => {
    const engine = new ReservationEngine([], null);
    const result = engine.validateMeeting(baseRequest);
    expect(result).toEqual(expect.objectContaining({ ok: false, message: "인증이 필요합니다." }));
  });

  test("과거 날짜는 거부한다", () => {
    const engine = new ReservationEngine([], USER_ID);
    const result = engine.validateMeeting({ ...baseRequest, date: "2000-01-01" });
    expect(result).toEqual(
      expect.objectContaining({ ok: false, message: "과거 날짜에는 예약할 수 없습니다." })
    );
  });

  test("참여자는 최소 3명이어야 한다", () => {
    const engine = new ReservationEngine([], USER_ID);
    const result = engine.validateMeeting({ ...baseRequest, participants: ["123"] });
    expect(result).toEqual(
      expect.objectContaining({ ok: false, message: "최소 3명 이상의 참여자가 필요합니다." })
    );
  });

  test("참여자 학번 형식을 검증한다", () => {
    const engine = new ReservationEngine([], USER_ID);
    const result = engine.validateMeeting({
      ...baseRequest,
      participants: ["123456789", "abc", "987654321"],
    });
    expect(result).toEqual(
      expect.objectContaining({ ok: false, message: "참여자 학번은 9자리 숫자여야 합니다." })
    );
  });

  test("동일 사용자의 회의실 중복 예약을 거부한다", () => {
    const existing = [meetingReservation({ date: FUTURE_DATE, slot: SLOT_9_10 })];
    const engine = new ReservationEngine(existing, USER_ID);
    const result = engine.validateMeeting(baseRequest);
    expect(result).toEqual(
      expect.objectContaining({ ok: false, message: "해당 시간에 이미 예약이 있습니다." })
    );
  });

  test("다른 시설 예약과 시간이 겹치면 거부한다", () => {
    const existing = [
      seatReservation({ date: FUTURE_DATE, slots: [SLOT_9_10], seatId: "SEAT-2" }),
    ];
    const engine = new ReservationEngine(existing, USER_ID);
    const result = engine.validateMeeting(baseRequest);
    expect(result).toEqual(
      expect.objectContaining({ ok: false, message: "다른 시설에서 같은 시간에 예약이 있습니다." })
    );
  });

  test("회의실이 이미 예약된 경우 거부한다", () => {
    const existing = [
      meetingReservation({
        date: FUTURE_DATE,
        slot: SLOT_9_10,
        roomId: "MR-1",
        studentId: "OTHER_USER",
      }),
    ];
    const engine = new ReservationEngine(existing, USER_ID);
    const result = engine.validateMeeting(baseRequest);
    expect(result).toEqual(
      expect.objectContaining({ ok: false, message: "해당 회의실이 이미 예약되었습니다." })
    );
  });

  test("회의실 일일 이용 한도를 검증한다", () => {
    const existing = [
      meetingReservation({ date: FUTURE_DATE, slot: SLOT_9_10 }),
      meetingReservation({ date: FUTURE_DATE, slot: SLOT_10_11 }),
    ];
    const engine = new ReservationEngine(existing, USER_ID);
    const result = engine.validateMeeting({ ...baseRequest, slot: SLOT_11_12 });
    expect(result).toEqual(
      expect.objectContaining({ ok: false, message: "회의실 일일 이용 한도를 초과했습니다." })
    );
  });

  test("회의실 주간 이용 한도를 검증한다", () => {
    const weeklyDates = ["2030-01-08", "2030-01-09", "2030-01-10", "2030-01-11", "2030-01-12"];
    const existing = weeklyDates.map((date, index) =>
      meetingReservation({ date, slot: slot(`slot-${index}`, 9 + index, 10 + index) })
    );
    const engine = new ReservationEngine(existing, USER_ID);
    const result = engine.validateMeeting({ ...baseRequest, date: "2030-01-13", slot: SLOT_9_10 });
    expect(result).toEqual(
      expect.objectContaining({ ok: false, message: "회의실 주간 이용 한도를 초과했습니다." })
    );
  });

  test("참여자 정보를 정규화해 성공을 반환한다", () => {
    const engine = new ReservationEngine([], USER_ID);
    const result = engine.validateMeeting({
      ...baseRequest,
      participants: [" 123456789 ", "987654321", "555666777", ""],
    });
    expect(result.ok).toBe(true);
    expect(result.participants).toEqual(["123456789", "987654321", "555666777"]);
  });
});

describe("열람실 좌석 예약 검증", () => {
  const seatRequest = {
    date: FUTURE_DATE,
    slots: [SLOT_13_15],
    seatId: "SEAT-1",
  };

  test("좌석 예약은 인증이 필요하다", () => {
    const engine = new ReservationEngine([], null);
    const result = engine.validateSeat(seatRequest);
    expect(result).toEqual(expect.objectContaining({ ok: false, message: "인증이 필요합니다." }));
  });

  test("최소 한 개 이상의 시간대를 요구한다", () => {
    const engine = new ReservationEngine([], USER_ID);
    const result = engine.validateSeat({ ...seatRequest, slots: [] });
    expect(result).toEqual(expect.objectContaining({ ok: false, message: "시간대를 선택해 주세요." }));
  });

  test("두 개 초과의 시간대를 거부한다", () => {
    const engine = new ReservationEngine([], USER_ID);
    const result = engine.validateSeat({
      ...seatRequest,
      slots: [SLOT_13_15, SLOT_15_17, SLOT_9_10],
    });
    expect(result).toEqual(
      expect.objectContaining({ ok: false, message: "하루 최대 4시간까지만 예약할 수 있습니다." })
    );
  });

  test("겹치는 시간대를 거부한다", () => {
    const engine = new ReservationEngine([], USER_ID);
    const result = engine.validateSeat({
      ...seatRequest,
      slots: [SLOT_13_15, SLOT_14_16],
    });
    expect(result).toEqual(
      expect.objectContaining({ ok: false, message: "겹치는 시간대는 선택할 수 없습니다." })
    );
  });

  test("과거 날짜 좌석 예약을 거부한다", () => {
    const engine = new ReservationEngine([], USER_ID);
    const result = engine.validateSeat({ ...seatRequest, date: "2001-01-01" });
    expect(result).toEqual(
      expect.objectContaining({ ok: false, message: "과거 날짜에는 예약할 수 없습니다." })
    );
  });

  test("운영 시간 외 예약을 거부한다", () => {
    const engine = new ReservationEngine([], USER_ID);
    const result = engine.validateSeat({ ...seatRequest, slots: [SLOT_17_19] });
    expect(result).toEqual(
      expect.objectContaining({ ok: false, message: "운영 시간 외에는 예약할 수 없습니다." })
    );
  });

  test("좌석 선택이 필수다", () => {
    const engine = new ReservationEngine([], USER_ID);
    const result = engine.validateSeat({ ...seatRequest, seatId: "" });
    expect(result).toEqual(
      expect.objectContaining({ ok: false, message: "좌석을 선택해 주세요." })
    );
  });

  test("좌석이 이미 예약된 경우 거부한다", () => {
    const existing = [seatReservation({ date: FUTURE_DATE, slots: [SLOT_13_15], seatId: "SEAT-1" })];
    const engine = new ReservationEngine(existing, USER_ID);
    const result = engine.validateSeat(seatRequest);
    expect(result).toEqual(
      expect.objectContaining({ ok: false, message: "해당 좌석이 이미 예약되었습니다." })
    );
  });

  test("회의실 예약과 시간이 겹치면 거부한다", () => {
    const existing = [meetingReservation({ date: FUTURE_DATE, slot: SLOT_13_15 })];
    const engine = new ReservationEngine(existing, USER_ID);
    const result = engine.validateSeat(seatRequest);
    expect(result).toEqual(
      expect.objectContaining({ ok: false, message: "다른 시설에서 같은 시간에 예약이 있습니다." })
    );
  });

  test("좌석 일일 이용 한도를 검증한다", () => {
    const existing = [
      seatReservation({ date: FUTURE_DATE, slots: [SLOT_09_11], seatId: "SEAT-2" }),
      seatReservation({ date: FUTURE_DATE, slots: [SLOT_11_13], seatId: "SEAT-3" }),
    ];
    const engine = new ReservationEngine(existing, USER_ID);
    const result = engine.validateSeat({ ...seatRequest, slots: [SLOT_13_15] });
    expect(result).toEqual(
      expect.objectContaining({ ok: false, message: "열람실 좌석 일일 이용 한도를 초과했습니다." })
    );
  });

  test("유효한 좌석 예약은 허용한다", () => {
    const engine = new ReservationEngine([], USER_ID);
    const result = engine.validateSeat(seatRequest);
    expect(result.ok).toBe(true);
  });
});

describe("ReservationEngine 유틸리티", () => {
  const formatDate = (date) => {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, "0");
    const day = String(date.getDate()).padStart(2, "0");
    return `${year}-${month}-${day}`;
  };

  test("slotsOverlap는 경계가 맞닿으면 겹치지 않는다", () => {
    expect(ReservationEngine.slotsOverlap(SLOT_9_10, SLOT_10_11)).toBe(false);
  });

  test("slotsOverlap는 부분 겹침을 감지한다", () => {
    expect(ReservationEngine.slotsOverlap(SLOT_09_11, SLOT_10_11)).toBe(true);
  });

  test("slotsListOverlap는 리스트 내 겹침을 감지한다", () => {
    expect(ReservationEngine.slotsListOverlap([SLOT_9_10, SLOT_09_11])).toBe(true);
    expect(ReservationEngine.slotsListOverlap([SLOT_9_10, SLOT_10_11])).toBe(false);
  });

  test("parseDateOnly는 유효하지 않은 입력을 null로 처리한다", () => {
    expect(ReservationEngine.parseDateOnly("2030-xx-01")).toBeNull();
  });

  test("isPastDate는 잘못된 날짜에서 false를 반환한다", () => {
    expect(ReservationEngine.isPastDate("invalid-date")).toBe(false);
  });

  test("getWeekRange는 월요일 시작/일요일 끝을 반환한다", () => {
    const target = ReservationEngine.parseDateOnly("2030-01-09");
    const { start, end } = ReservationEngine.getWeekRange(target);

    expect(start.getDay()).toBe(1);
    expect(end.getDay()).toBe(0);
    expect(target.getTime()).toBeGreaterThanOrEqual(start.getTime());
    expect(target.getTime()).toBeLessThanOrEqual(end.getTime());
  });

  test("getMeetingHoursForWeek는 같은 주의 예약만 합산한다", () => {
    const baseDate = "2030-01-09";
    const { start, end } = ReservationEngine.getWeekRange(ReservationEngine.parseDateOnly(baseDate));
    const mid = new Date(start);
    mid.setDate(start.getDate() + 2);
    const nextWeek = new Date(end);
    nextWeek.setDate(end.getDate() + 1);

    const reservations = [
      meetingReservation({ date: formatDate(start), slot: SLOT_9_10 }),
      meetingReservation({ date: formatDate(mid), slot: SLOT_10_11 }),
      meetingReservation({ date: formatDate(nextWeek), slot: SLOT_11_12 }),
    ];

    const total = ReservationEngine.getMeetingHoursForWeek(reservations, USER_ID, baseDate);
    expect(total).toBe(2);
  });

  test("getMeetingHoursForWeek는 잘못된 날짜면 0을 반환한다", () => {
    const total = ReservationEngine.getMeetingHoursForWeek([], USER_ID, "invalid-date");
    expect(total).toBe(0);
  });

  test("isSeatFree는 좌석이나 슬롯이 없으면 false를 반환한다", () => {
    expect(ReservationEngine.isSeatFree([], FUTURE_DATE, "", [SLOT_13_15])).toBe(false);
    expect(ReservationEngine.isSeatFree([], FUTURE_DATE, "SEAT-1", [])).toBe(false);
  });

  test("isSeatFree는 같은 좌석의 겹치는 예약을 거부한다", () => {
    const existing = [
      seatReservation({ date: FUTURE_DATE, slots: [SLOT_13_15], seatId: "SEAT-1" }),
    ];

    expect(ReservationEngine.isSeatFree(existing, FUTURE_DATE, "SEAT-1", [SLOT_14_16])).toBe(false);
    expect(ReservationEngine.isSeatFree(existing, FUTURE_DATE, "SEAT-2", [SLOT_14_16])).toBe(true);
  });

  test("findUserConflict는 사용자 겹침 예약을 반환한다", () => {
    const existing = [
      meetingReservation({ date: FUTURE_DATE, slot: SLOT_9_10, studentId: USER_ID }),
      seatReservation({ date: FUTURE_DATE, slots: [SLOT_13_15], studentId: "OTHER_USER" }),
    ];

    const conflict = ReservationEngine.findUserConflict(
      existing,
      USER_ID,
      FUTURE_DATE,
      [SLOT_09_11]
    );

    expect(conflict).toEqual(expect.objectContaining({ spaceType: "MEETING" }));
    expect(ReservationEngine.findUserConflict(existing, null, FUTURE_DATE, [SLOT_09_11])).toBeNull();
  });

  test("isRoomReserved는 동일 회의실과 슬롯만 확인한다", () => {
    const existing = [meetingReservation({ date: FUTURE_DATE, slot: SLOT_9_10, roomId: "MR-1" })];

    expect(ReservationEngine.isRoomReserved(existing, FUTURE_DATE, "MR-1", SLOT_9_10.id)).toBe(true);
    expect(ReservationEngine.isRoomReserved(existing, FUTURE_DATE, "MR-2", SLOT_9_10.id)).toBe(false);
  });
});
