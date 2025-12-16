// js/reservation-engine.js

(function (global) {
  class ReservationEngine {
    constructor(reservations = [], userId) {
      this.reservations = Array.isArray(reservations) ? reservations : [];
      this.userId = userId || null;
    }

    validateMeeting(request = {}) {
      const { date, slot, roomId, participants = [] } = request;
      if (!this.userId) return ReservationEngine.failure("AUTH_REQUIRED", "Authentication required");
      if (!date || !slot || !roomId) {
        return ReservationEngine.failure("INVALID_REQUEST", "Missing reservation details");
      }
      if (ReservationEngine.isPastDate(date)) {
        return ReservationEngine.failure("PAST_DATE", "Past date reservation not allowed");
      }
      if (!ReservationEngine.isWithinOperatingHours(slot)) {
        return ReservationEngine.failure("OUTSIDE_HOURS", "Outside operation hours");
      }

      const normalizedParticipants = participants.map((value) => (value || "").trim()).filter(Boolean);
      if (normalizedParticipants.length < 3) {
        return ReservationEngine.failure("PARTICIPANT_MIN", "Minimum 3 participants required");
      }
      if (normalizedParticipants.some((id) => !/^\d{9}$/.test(id))) {
        return ReservationEngine.failure("PARTICIPANT_FORMAT", "Participant IDs must be 9 digits");
      }

      const conflict = ReservationEngine.findUserConflict(this.reservations, this.userId, date, [slot]);
      if (conflict) {
        const message =
          conflict.spaceType === "MEETING"
            ? "User already has reservation at this time"
            : "Another facility already reserved at this time";
        return ReservationEngine.failure("USER_CONFLICT", message);
      }

      if (ReservationEngine.isRoomReserved(this.reservations, date, roomId, slot.id)) {
        return ReservationEngine.failure("ROOM_BOOKED", "Meeting room already reserved");
      }

      const slotDuration = ReservationEngine.getSlotDurationHours(slot);
      const dailyHours = ReservationEngine.getMeetingHoursForDate(this.reservations, this.userId, date);
      if (dailyHours + slotDuration > 2) {
        return ReservationEngine.failure("DAILY_LIMIT", "Daily meeting room limit exceeded");
      }

      const weeklyHours = ReservationEngine.getMeetingHoursForWeek(this.reservations, this.userId, date);
      if (weeklyHours + slotDuration > 5) {
        return ReservationEngine.failure("WEEKLY_LIMIT", "Weekly meeting room limit exceeded");
      }

      return ReservationEngine.success({ participants: normalizedParticipants });
    }

    validateSeat(request = {}) {
      const { date, slots = [], seatId } = request;
      if (!this.userId) return ReservationEngine.failure("AUTH_REQUIRED", "Authentication required");
      if (!date) return ReservationEngine.failure("INVALID_REQUEST", "Missing reservation date");

      const normalizedSlots = Array.isArray(slots) ? slots : [];
      if (normalizedSlots.length === 0) {
        return ReservationEngine.failure("SLOT_REQUIRED", "No time slot selected");
      }
      if (normalizedSlots.length > 2) {
        return ReservationEngine.failure("DAILY_LIMIT", "Maximum 4 hours per day");
      }
      if (ReservationEngine.slotsListOverlap(normalizedSlots)) {
        return ReservationEngine.failure("SLOT_OVERLAP", "Overlapping time slots");
      }
      if (ReservationEngine.isPastDate(date)) {
        return ReservationEngine.failure("PAST_DATE", "Past date reservation not allowed");
      }
      if (!normalizedSlots.every((slot) => ReservationEngine.isWithinOperatingHours(slot))) {
        return ReservationEngine.failure("OUTSIDE_HOURS", "Outside operation hours");
      }
      if (!seatId) {
        return ReservationEngine.failure("SEAT_REQUIRED", "Seat selection required");
      }

      if (!ReservationEngine.isSeatFree(this.reservations, date, seatId, normalizedSlots)) {
        return ReservationEngine.failure("SEAT_BOOKED", "Seat already reserved");
      }

      const conflict = ReservationEngine.findUserConflict(this.reservations, this.userId, date, normalizedSlots);
      if (conflict) {
        const message =
          conflict.spaceType === "MEETING"
            ? "Another facility already reserved at this time"
            : "User already has reservation at this time";
        return ReservationEngine.failure("USER_CONFLICT", message);
      }

      const totalHours = normalizedSlots.reduce(
        (sum, slot) => sum + ReservationEngine.getSlotDurationHours(slot),
        0
      );
      const seatHours = ReservationEngine.getSeatHoursForDate(this.reservations, this.userId, date);
      if (seatHours + totalHours > 4) {
        return ReservationEngine.failure("DAILY_LIMIT", "Daily seat reservation limit exceeded");
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
