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

describe("ReservationEngine.validateMeeting", () => {
  const baseRequest = {
    date: FUTURE_DATE,
    slot: SLOT_9_10,
    roomId: "MR-1",
    participants: ["123456789", "987654321", "111222333"],
  };

  test("rejects unauthenticated requests", () => {
    const engine = new ReservationEngine([], null);
    const result = engine.validateMeeting(baseRequest);
    expect(result).toEqual(
      expect.objectContaining({ ok: false, message: "Authentication required" })
    );
  });

  test("rejects past dates", () => {
    const engine = new ReservationEngine([], USER_ID);
    const result = engine.validateMeeting({ ...baseRequest, date: "2000-01-01" });
    expect(result).toEqual(
      expect.objectContaining({ ok: false, message: "Past date reservation not allowed" })
    );
  });

  test("requires at least 3 participants", () => {
    const engine = new ReservationEngine([], USER_ID);
    const result = engine.validateMeeting({ ...baseRequest, participants: ["123"] });
    expect(result).toEqual(
      expect.objectContaining({ ok: false, message: "Minimum 3 participants required" })
    );
  });

  test("validates participant format", () => {
    const engine = new ReservationEngine([], USER_ID);
    const result = engine.validateMeeting({
      ...baseRequest,
      participants: ["123456789", "abc", "987654321"],
    });
    expect(result).toEqual(
      expect.objectContaining({ ok: false, message: "Participant IDs must be 9 digits" })
    );
  });

  test("rejects overlapping reservations for same user (meeting)", () => {
    const existing = [meetingReservation({ date: FUTURE_DATE, slot: SLOT_9_10 })];
    const engine = new ReservationEngine(existing, USER_ID);
    const result = engine.validateMeeting(baseRequest);
    expect(result).toEqual(
      expect.objectContaining({ ok: false, message: "User already has reservation at this time" })
    );
  });

  test("rejects overlapping reservations from another facility", () => {
    const existing = [
      seatReservation({ date: FUTURE_DATE, slots: [SLOT_9_10], seatId: "SEAT-2" }),
    ];
    const engine = new ReservationEngine(existing, USER_ID);
    const result = engine.validateMeeting(baseRequest);
    expect(result).toEqual(
      expect.objectContaining({ ok: false, message: "Another facility already reserved at this time" })
    );
  });

  test("rejects when room already reserved", () => {
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
      expect.objectContaining({ ok: false, message: "Meeting room already reserved" })
    );
  });

  test("enforces daily meeting limit", () => {
    const existing = [
      meetingReservation({ date: FUTURE_DATE, slot: SLOT_9_10 }),
      meetingReservation({ date: FUTURE_DATE, slot: SLOT_10_11 }),
    ];
    const engine = new ReservationEngine(existing, USER_ID);
    const result = engine.validateMeeting({ ...baseRequest, slot: SLOT_11_12 });
    expect(result).toEqual(
      expect.objectContaining({ ok: false, message: "Daily meeting room limit exceeded" })
    );
  });

  test("enforces weekly meeting limit", () => {
    const weeklyDates = ["2030-01-08", "2030-01-09", "2030-01-10", "2030-01-11", "2030-01-12"];
    const existing = weeklyDates.map((date, index) =>
      meetingReservation({ date, slot: slot(`slot-${index}`, 9 + index, 10 + index) })
    );
    const engine = new ReservationEngine(existing, USER_ID);
    const result = engine.validateMeeting({ ...baseRequest, date: "2030-01-13", slot: SLOT_9_10 });
    expect(result).toEqual(
      expect.objectContaining({ ok: false, message: "Weekly meeting room limit exceeded" })
    );
  });

  test("returns success with normalized participants", () => {
    const engine = new ReservationEngine([], USER_ID);
    const result = engine.validateMeeting({
      ...baseRequest,
      participants: [" 123456789 ", "987654321", "555666777", ""],
    });
    expect(result.ok).toBe(true);
    expect(result.participants).toEqual(["123456789", "987654321", "555666777"]);
  });
});

describe("ReservationEngine.validateSeat", () => {
  const seatRequest = {
    date: FUTURE_DATE,
    slots: [SLOT_13_15],
    seatId: "SEAT-1",
  };

  test("requires authentication", () => {
    const engine = new ReservationEngine([], null);
    const result = engine.validateSeat(seatRequest);
    expect(result).toEqual(
      expect.objectContaining({ ok: false, message: "Authentication required" })
    );
  });

  test("requires at least one slot", () => {
    const engine = new ReservationEngine([], USER_ID);
    const result = engine.validateSeat({ ...seatRequest, slots: [] });
    expect(result).toEqual(expect.objectContaining({ ok: false, message: "No time slot selected" }));
  });

  test("rejects more than two slots", () => {
    const engine = new ReservationEngine([], USER_ID);
    const result = engine.validateSeat({
      ...seatRequest,
      slots: [SLOT_13_15, SLOT_15_17, SLOT_9_10],
    });
    expect(result).toEqual(expect.objectContaining({ ok: false, message: "Maximum 4 hours per day" }));
  });

  test("rejects overlapping slots", () => {
    const engine = new ReservationEngine([], USER_ID);
    const result = engine.validateSeat({
      ...seatRequest,
      slots: [SLOT_13_15, SLOT_14_16],
    });
    expect(result).toEqual(
      expect.objectContaining({ ok: false, message: "Overlapping time slots" })
    );
  });

  test("rejects past dates", () => {
    const engine = new ReservationEngine([], USER_ID);
    const result = engine.validateSeat({ ...seatRequest, date: "2001-01-01" });
    expect(result).toEqual(
      expect.objectContaining({ ok: false, message: "Past date reservation not allowed" })
    );
  });

  test("rejects outside operating hours", () => {
    const engine = new ReservationEngine([], USER_ID);
    const result = engine.validateSeat({ ...seatRequest, slots: [SLOT_17_19] });
    expect(result).toEqual(
      expect.objectContaining({ ok: false, message: "Outside operation hours" })
    );
  });

  test("requires seat selection", () => {
    const engine = new ReservationEngine([], USER_ID);
    const result = engine.validateSeat({ ...seatRequest, seatId: "" });
    expect(result).toEqual(
      expect.objectContaining({ ok: false, message: "Seat selection required" })
    );
  });

  test("rejects when seat already reserved", () => {
    const existing = [seatReservation({ date: FUTURE_DATE, slots: [SLOT_13_15], seatId: "SEAT-1" })];
    const engine = new ReservationEngine(existing, USER_ID);
    const result = engine.validateSeat(seatRequest);
    expect(result).toEqual(
      expect.objectContaining({ ok: false, message: "Seat already reserved" })
    );
  });

  test("rejects conflicts with meeting reservation", () => {
    const existing = [meetingReservation({ date: FUTURE_DATE, slot: SLOT_13_15 })];
    const engine = new ReservationEngine(existing, USER_ID);
    const result = engine.validateSeat(seatRequest);
    expect(result).toEqual(
      expect.objectContaining({ ok: false, message: "Another facility already reserved at this time" })
    );
  });

  test("rejects seat daily limit violations", () => {
    const existing = [
      seatReservation({ date: FUTURE_DATE, slots: [SLOT_09_11], seatId: "SEAT-2" }),
      seatReservation({ date: FUTURE_DATE, slots: [SLOT_11_13], seatId: "SEAT-3" }),
    ];
    const engine = new ReservationEngine(existing, USER_ID);
    const result = engine.validateSeat({ ...seatRequest, slots: [SLOT_13_15] });
    expect(result).toEqual(
      expect.objectContaining({ ok: false, message: "Daily seat reservation limit exceeded" })
    );
  });

  test("accepts valid seat reservation", () => {
    const engine = new ReservationEngine([], USER_ID);
    const result = engine.validateSeat(seatRequest);
    expect(result.ok).toBe(true);
  });
});
