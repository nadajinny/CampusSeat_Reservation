// js/reservation-engine.js

(function (global) {
  class ReservationEngine {
    constructor(reservations = [], userId) {
      this.reservations = Array.isArray(reservations) ? reservations : [];
      this.userId = userId || null;
    }

    validateMeeting(request = {}) {
      const { date, slot, roomId, participants = [] } = request;
      if (!this.userId) return ReservationEngine.failure("AUTH_REQUIRED", "인증이 필요합니다.");
      if (!date || !slot || !roomId) {
        return ReservationEngine.failure("INVALID_REQUEST", "예약 정보가 누락되었습니다.");
      }
      if (ReservationEngine.isPastDate(date)) {
        return ReservationEngine.failure("PAST_DATE", "과거 날짜에는 예약할 수 없습니다.");
      }
      if (!ReservationEngine.isWithinOperatingHours(slot)) {
        return ReservationEngine.failure("OUTSIDE_HOURS", "운영 시간 외에는 예약할 수 없습니다.");
      }

      const normalizedParticipants = participants.map((value) => (value || "").trim()).filter(Boolean);
      if (normalizedParticipants.length < 3) {
        return ReservationEngine.failure("PARTICIPANT_MIN", "최소 3명 이상의 참여자가 필요합니다.");
      }
      if (normalizedParticipants.some((id) => !/^\d{9}$/.test(id))) {
        return ReservationEngine.failure("PARTICIPANT_FORMAT", "참여자 학번은 9자리 숫자여야 합니다.");
      }

      const conflict = ReservationEngine.findUserConflict(this.reservations, this.userId, date, [slot]);
      if (conflict) {
        const message =
          conflict.spaceType === "MEETING"
            ? "해당 시간에 이미 예약이 있습니다."
            : "다른 시설에서 같은 시간에 예약이 있습니다.";
        return ReservationEngine.failure("USER_CONFLICT", message);
      }

      if (ReservationEngine.isRoomReserved(this.reservations, date, roomId, slot.id)) {
        return ReservationEngine.failure("ROOM_BOOKED", "해당 회의실이 이미 예약되었습니다.");
      }

      const slotDuration = ReservationEngine.getSlotDurationHours(slot);
      const dailyHours = ReservationEngine.getMeetingHoursForDate(this.reservations, this.userId, date);
      if (dailyHours + slotDuration > 2) {
        return ReservationEngine.failure("DAILY_LIMIT", "회의실 일일 이용 한도를 초과했습니다.");
      }

      const weeklyHours = ReservationEngine.getMeetingHoursForWeek(this.reservations, this.userId, date);
      if (weeklyHours + slotDuration > 5) {
        return ReservationEngine.failure("WEEKLY_LIMIT", "회의실 주간 이용 한도를 초과했습니다.");
      }

      return ReservationEngine.success({ participants: normalizedParticipants });
    }

    validateSeat(request = {}) {
      const { date, slots = [], seatId } = request;
      if (!this.userId) return ReservationEngine.failure("AUTH_REQUIRED", "인증이 필요합니다.");
      if (!date) return ReservationEngine.failure("INVALID_REQUEST", "예약 날짜가 누락되었습니다.");

      const normalizedSlots = Array.isArray(slots) ? slots : [];
      if (normalizedSlots.length === 0) {
        return ReservationEngine.failure("SLOT_REQUIRED", "시간대를 선택해 주세요.");
      }
      if (normalizedSlots.length > 2) {
        return ReservationEngine.failure("DAILY_LIMIT", "하루 최대 4시간까지만 예약할 수 있습니다.");
      }
      if (ReservationEngine.slotsListOverlap(normalizedSlots)) {
        return ReservationEngine.failure("SLOT_OVERLAP", "겹치는 시간대는 선택할 수 없습니다.");
      }
      if (ReservationEngine.isPastDate(date)) {
        return ReservationEngine.failure("PAST_DATE", "과거 날짜에는 예약할 수 없습니다.");
      }
      if (!normalizedSlots.every((slot) => ReservationEngine.isWithinOperatingHours(slot))) {
        return ReservationEngine.failure("OUTSIDE_HOURS", "운영 시간 외에는 예약할 수 없습니다.");
      }
      if (!seatId) {
        return ReservationEngine.failure("SEAT_REQUIRED", "좌석을 선택해 주세요.");
      }

      if (!ReservationEngine.isSeatFree(this.reservations, date, seatId, normalizedSlots)) {
        return ReservationEngine.failure("SEAT_BOOKED", "해당 좌석이 이미 예약되었습니다.");
      }

      const conflict = ReservationEngine.findUserConflict(this.reservations, this.userId, date, normalizedSlots);
      if (conflict) {
        const message =
          conflict.spaceType === "MEETING"
            ? "다른 시설에서 같은 시간에 예약이 있습니다."
            : "해당 시간에 이미 예약이 있습니다.";
        return ReservationEngine.failure("USER_CONFLICT", message);
      }

      const totalHours = normalizedSlots.reduce(
        (sum, slot) => sum + ReservationEngine.getSlotDurationHours(slot),
        0
      );
      const seatHours = ReservationEngine.getSeatHoursForDate(this.reservations, this.userId, date);
      if (seatHours + totalHours > 4) {
        return ReservationEngine.failure("DAILY_LIMIT", "열람실 좌석 일일 이용 한도를 초과했습니다.");
      }

      return ReservationEngine.success();
    }

    static isSeatFree(reservations, date, seatId, targetSlots) {
      if (!seatId || !Array.isArray(targetSlots) || targetSlots.length === 0) return false;
      return targetSlots.every((targetSlot) => {
        return !reservations.some((reservation) => {
          if (
            reservation.spaceType !== "READING" ||
            reservation.date !== date ||
            reservation.seatId !== seatId
          ) {
            return false;
          }
          return reservation.timeSlots.some((slot) => ReservationEngine.slotsOverlap(slot, targetSlot));
        });
      });
    }

    static isRoomReserved(reservations, date, roomId, slotId) {
      return reservations.some(
        (reservation) =>
          reservation.spaceType === "MEETING" &&
          reservation.date === date &&
          reservation.roomId === roomId &&
          reservation.timeSlots.some((slot) => slot.id === slotId)
      );
    }

    static findUserConflict(reservations, userId, date, targetSlots) {
      if (!userId) return null;
      return (
        reservations.find(
          (reservation) =>
            reservation.studentId === userId &&
            reservation.date === date &&
            reservation.timeSlots.some((slot) =>
              targetSlots.some((target) => ReservationEngine.slotsOverlap(slot, target))
            )
        ) || null
      );
    }

    static slotsOverlap(a, b) {
      return a.startMinutes < b.endMinutes && b.startMinutes < a.endMinutes;
    }

    static slotsListOverlap(slots) {
      for (let i = 0; i < slots.length; i += 1) {
        for (let j = i + 1; j < slots.length; j += 1) {
          if (ReservationEngine.slotsOverlap(slots[i], slots[j])) {
            return true;
          }
        }
      }
      return false;
    }

    static getSlotDurationHours(slot) {
      return (slot.endMinutes - slot.startMinutes) / 60;
    }

    static getReservationDurationHours(reservation) {
      return reservation.timeSlots.reduce(
        (sum, slot) => sum + ReservationEngine.getSlotDurationHours(slot),
        0
      );
    }

    static getMeetingHoursForDate(reservations, userId, dateStr) {
      return reservations
        .filter((reservation) => reservation.studentId === userId)
        .filter((reservation) => reservation.spaceType === "MEETING" && reservation.date === dateStr)
        .reduce((sum, reservation) => sum + ReservationEngine.getReservationDurationHours(reservation), 0);
    }

    static getMeetingHoursForWeek(reservations, userId, dateStr) {
      const targetDate = ReservationEngine.parseDateOnly(dateStr);
      if (!targetDate) return 0;
      const { start, end } = ReservationEngine.getWeekRange(targetDate);

      return reservations
        .filter((reservation) => reservation.studentId === userId && reservation.spaceType === "MEETING")
        .filter((reservation) => {
          const resDate = ReservationEngine.parseDateOnly(reservation.date);
          return resDate && resDate >= start && resDate <= end;
        })
        .reduce((sum, reservation) => sum + ReservationEngine.getReservationDurationHours(reservation), 0);
    }

    static getSeatHoursForDate(reservations, userId, dateStr) {
      return reservations
        .filter((reservation) => reservation.studentId === userId)
        .filter((reservation) => reservation.spaceType === "READING" && reservation.date === dateStr)
        .reduce((sum, reservation) => sum + ReservationEngine.getReservationDurationHours(reservation), 0);
    }

    static parseDateOnly(dateStr) {
      if (!dateStr) return null;
      const [year, month, day] = dateStr.split("-").map(Number);
      if ([year, month, day].some((value) => Number.isNaN(value))) {
        return null;
      }
      return new Date(year, month - 1, day);
    }

    static isPastDate(dateStr) {
      const target = ReservationEngine.parseDateOnly(dateStr);
      if (!target) return false;
      const today = new Date();
      today.setHours(0, 0, 0, 0);
      target.setHours(0, 0, 0, 0);
      return target < today;
    }

    static getWeekRange(date) {
      const start = new Date(date);
      const day = start.getDay();
      const diffToMonday = (day + 6) % 7;
      start.setDate(start.getDate() - diffToMonday);
      start.setHours(0, 0, 0, 0);

      const end = new Date(start);
      end.setDate(end.getDate() + 6);
      end.setHours(23, 59, 59, 999);

      return { start, end };
    }

    static isWithinOperatingHours(slot) {
      return slot.startMinutes >= 9 * 60 && slot.endMinutes <= 18 * 60;
    }

    static success(extra = {}) {
      return { ok: true, ...extra };
    }

    static failure(code, message) {
      return { ok: false, code, message };
    }
  }

  if (typeof module !== "undefined" && module.exports) {
    module.exports = { ReservationEngine };
  } else if (global) {
    global.ReservationEngine = ReservationEngine;
  }
})(typeof window !== "undefined" ? window : globalThis);
