// js/app.js

(() => {
  const STORAGE_KEY = "campusReservations";
  const PENDING_KEY = "pendingReservation";
  const MEETING_ROOMS = [
    { id: "MR-1", name: "회의실 1", capacity: 6 },
    { id: "MR-2", name: "회의실 2", capacity: 8 },
    { id: "MR-3", name: "회의실 3", capacity: 10 },
  ];

  const MEETING_SLOTS = createSlots({ startHour: 9, endHour: 18, duration: 1 });
  const READING_SLOTS = createSlots({ startHour: 9, endHour: 18, duration: 2 });

  const READING_SEATS = Array.from({ length: 15 }, (_, idx) => {
    const number = idx + 1;
    const label = `좌석 ${number}`;
    return { id: `SEAT-${number}`, label };
  });

  const state = {
    spaceType: null,
    date: "",
    selectedMeetingSlot: null,
    selectedMeetingRoom: null,
    participants: ["", "", ""],
    selectedReadingSlots: [],
    selectedSeat: null,
  };

  let studentId = null;
  const ReservationEngineClass = window.ReservationEngine;

  document.addEventListener("DOMContentLoaded", () => {
    if (!ReservationEngineClass) {
      console.error("시스템을 실행하기 위해 ReservationEngine이 필요합니다.");
      alert("시스템 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.");
      return;
    }

    studentId = sessionStorage.getItem("studentId");

    if (!studentId) {
      alert("로그인이 필요합니다.");
      window.location.href = "login.html";
      return;
    }

    renderUserSummary(studentId);
    bindLogout();

    initAvailabilityFlow();
    initMeetingReservationPage();
    initSeatReservationPage();
    renderMyReservations();
  });

  function createSlots({ startHour, endHour, duration }) {
    const slots = [];
    for (let hour = startHour; hour + duration <= endHour; hour += 1) {
      const startMinutes = hour * 60;
      const endMinutes = (hour + duration) * 60;
      slots.push({
        id: `${hour}-${hour + duration}`,
        label: `${formatHour(hour)}:00 ~ ${formatHour(hour + duration)}:00`,
        startMinutes,
        endMinutes,
      });
    }
    return slots;
  }

  function formatHour(value) {
    return String(value).padStart(2, "0");
  }

  function renderUserSummary(id) {
    const textEl = document.getElementById("studentIdText");
    if (textEl) {
      textEl.textContent = id;
    }
  }

  function bindLogout() {
    const button = document.getElementById("logoutBtn");
    if (!button) return;
    button.addEventListener("click", () => {
      sessionStorage.clear();
      window.location.href = "login.html";
    });
  }

  function initAvailabilityFlow() {
    const filters = document.getElementById("availability-filters");
    if (!filters) return;

    const dateInput = document.getElementById("reservationDate");
    const typeInputs = document.querySelectorAll('input[name="spaceType"]');

    typeInputs.forEach((input) => {
      input.addEventListener("change", () => {
        state.spaceType = input.value;
        resetFlowState();
        runAvailabilityFlow();
      });
    });

    if (dateInput) {
      dateInput.addEventListener("change", () => {
        state.date = dateInput.value;
        resetFlowState();
        runAvailabilityFlow();
      });
    }

    const proceedButton = document.getElementById("readingProceedBtn");
    if (proceedButton) {
      proceedButton.addEventListener("click", () => {
        if (state.selectedReadingSlots.length === 0) return;
        setPendingReservation({
          type: "READING",
          date: state.date,
          slotIds: [...state.selectedReadingSlots],
        });
        window.location.href = "seat-reservation.html";
      });
    }

    updateReadingProceedButton();
    runAvailabilityFlow();
  }

  function initMeetingReservationPage() {
    const page = document.getElementById("meeting-room-page");
    if (!page) return;

    const contextError = document.getElementById("meeting-context-error");
    const pending = getPendingReservation();

    if (!pending || pending.type !== "MEETING" || !pending.slotId || !pending.date) {
      if (contextError) contextError.classList.remove("hidden");
      toggleSection("meeting-room-section", false);
      toggleSection("meeting-summary-section", false);
      return;
    }

    state.spaceType = "MEETING";
    state.date = pending.date;
    state.selectedMeetingSlot = pending.slotId;
    state.selectedMeetingRoom = null;
    state.participants = ["", "", ""];

    const slot = getSlotById(state.selectedMeetingSlot, "MEETING");
    const dateEl = document.getElementById("meeting-context-date");
    const slotEl = document.getElementById("meeting-context-slot");
    if (dateEl) dateEl.textContent = `예약 날짜: ${state.date}`;
    if (slotEl) slotEl.textContent = slot ? `예약 시간: ${slot.label}` : "예약 시간을 불러올 수 없습니다.";

    toggleSection("meeting-room-section", true);
    renderMeetingRooms();
    renderMeetingSummary();
  }

  function initSeatReservationPage() {
    const page = document.getElementById("seat-reservation-page");
    if (!page) return;

    const contextError = document.getElementById("reading-context-error");
    const pending = getPendingReservation();

    if (
      !pending ||
      pending.type !== "READING" ||
      !pending.slotIds ||
      !Array.isArray(pending.slotIds) ||
      pending.slotIds.length === 0
    ) {
      if (contextError) contextError.classList.remove("hidden");
      toggleSection("reading-seat-section", false);
      toggleSection("reading-summary-section", false);
      return;
    }

    state.spaceType = "READING";
    state.date = pending.date;
    state.selectedReadingSlots = pending.slotIds;
    state.selectedSeat = null;

    const listEl = document.getElementById("reading-context-slots");
    if (listEl) {
      const listItems = state.selectedReadingSlots
        .map((slotId) => {
          const slot = getSlotById(slotId, "READING");
          return slot ? `<li>${state.date} ${slot.label}</li>` : "";
        })
        .filter(Boolean)
        .join("");
      listEl.innerHTML = listItems || "<li>선택한 시간 정보를 불러올 수 없습니다.</li>";
    }

    toggleSection("reading-seat-section", true);
    renderSeatMap();
    renderReadingSummary();

    const randomSeatBtn = document.getElementById("randomSeatBtn");
    if (randomSeatBtn) {
      randomSeatBtn.addEventListener("click", handleRandomSeatAssignment);
    }
  }


  function runAvailabilityFlow() {
    const ready = Boolean(state.spaceType && state.date);

    toggleSection("meeting-time-section", ready && state.spaceType === "MEETING");
    toggleSection("reading-time-section", ready && state.spaceType === "READING");

    if (!ready) {
      clearElement("meeting-time-list");
      clearElement("reading-time-grid");
      updateReadingProceedButton();
      return;
    }

    if (state.spaceType === "MEETING") {
      renderMeetingTimeSlots();
    } else if (state.spaceType === "READING") {
      renderReadingTimeSlots();
    }
  }

  function resetFlowState({ preserveFilters = true } = {}) {
    state.selectedMeetingSlot = null;
    state.selectedMeetingRoom = null;
    state.participants = ["", "", ""];
    state.selectedReadingSlots = [];
    state.selectedSeat = null;

    if (!preserveFilters) {
      state.spaceType = null;
      state.date = "";
      const dateInput = document.getElementById("reservationDate");
      if (dateInput) dateInput.value = "";
      document.querySelectorAll('input[name="spaceType"]').forEach((input) => {
        input.checked = false;
      });
    }

    clearElement("meeting-time-list");
    clearElement("reading-time-grid");
    updateReadingProceedButton();
  }

  function renderMeetingTimeSlots() {
    const listEl = document.getElementById("meeting-time-list");
    if (!listEl) return;

    const reservations = loadReservations();
    listEl.innerHTML = "";

    MEETING_SLOTS.forEach((slot) => {
      const row = document.createElement("div");
      row.className = "time-slot-row";

      const label = document.createElement("strong");
      label.textContent = slot.label;

      const button = document.createElement("button");
      button.type = "button";

      const available = isMeetingSlotAvailable(reservations, slot);
      button.textContent = available ? "예약 진행" : "예약 불가";
      button.disabled = !available;

      if (available) {
        button.addEventListener("click", () => {
          goToMeetingReservation(slot);
        });
      }

      row.append(label, button);
      listEl.appendChild(row);
    });
  }

  function goToMeetingReservation(slot) {
    if (!state.date) return;
    setPendingReservation({
      type: "MEETING",
      date: state.date,
      slotId: slot.id,
    });
    window.location.href = "meeting-room-reservation.html";
  }

  function renderMeetingRooms() {
    const listEl = document.getElementById("meeting-room-list");
    if (!listEl) return;

    if (!state.selectedMeetingSlot) {
      listEl.innerHTML = "";
      toggleSection("meeting-room-section", false);
      return;
    }

    const reservations = loadReservations();
    listEl.innerHTML = "";
    toggleSection("meeting-room-section", true);

    MEETING_ROOMS.forEach((room) => {
      const card = document.createElement("div");
      card.className = "room-card";

      const info = document.createElement("div");
      info.innerHTML = `<strong>${room.name}</strong><p class="notice">수용 인원 ${room.capacity}명</p>`;

      const button = document.createElement("button");
      button.type = "button";

      const available = isRoomAvailable(reservations, state.date, room.id, state.selectedMeetingSlot);
      const selected = state.selectedMeetingRoom === room.id;

      button.textContent = available ? (selected ? "선택됨" : "예약 가능") : "예약 불가";
      if (!available) {
        button.classList.add("blocked");
      }

      button.addEventListener("click", () => {
        if (!available) {
          alert("해당 회의실은 현재 예약할 수 없습니다.");
          return;
        }
        state.selectedMeetingRoom = room.id;
        renderMeetingRooms();
        renderMeetingSummary();
        runAvailabilityFlow();
      });

      card.append(info, button);
      listEl.appendChild(card);
    });
  }

  function renderMeetingSummary() {
    const summarySection = document.getElementById("meeting-summary");
    if (!summarySection) return;

    if (!state.selectedMeetingSlot || !state.selectedMeetingRoom) {
      summarySection.innerHTML = "";
      toggleSection("meeting-summary-section", false);
      return;
    }

    const slot = getSlotById(state.selectedMeetingSlot, "MEETING");
    const room = MEETING_ROOMS.find((item) => item.id === state.selectedMeetingRoom);

    if (!slot || !room) return;

    const participantFields = state.participants
      .map(
        (value, index) => `
          <div class="participant-row">
            <label for="participant-${index}">참여자 ${index + 1}</label>
            <input
              type="text"
              id="participant-${index}"
              data-participant-index="${index}"
              placeholder="예: 20230000${index + 1}"
              pattern="\\d{9}"
              inputmode="numeric"
              maxlength="9"
              value="${value}"
              required
            />
          </div>
        `
      )
      .join("");

    summarySection.innerHTML = `
      <p><strong>공간</strong> : ${room.name}</p>
      <p><strong>일시</strong> : ${state.date} ${slot.label}</p>
      <div id="participantInputGroup">
        <p><strong>참여자 목록</strong> (각 칸에 학번 9자리를 입력하세요)</p>
        ${participantFields}
      </div>
      <p class="error" id="meeting-error" aria-live="polite"></p>
      <button type="button" id="submitMeetingReservation">예약 제출</button>
    `;
    toggleSection("meeting-summary-section", true);
    scrollToSection("meeting-summary-section");

    const participantInputs = summarySection.querySelectorAll("input[data-participant-index]");
    participantInputs.forEach((input) => {
      input.addEventListener("input", (event) => {
        const target = event.target;
        const index = Number(target.dataset.participantIndex);
        if (Number.isNaN(index)) return;
        state.participants[index] = target.value;
      });
    });

    const submitButton = document.getElementById("submitMeetingReservation");
    if (submitButton) {
      submitButton.addEventListener("click", handleMeetingReservationSubmit);
    }
  }

  function handleMeetingReservationSubmit() {
    const errorEl = document.getElementById("meeting-error");
    if (errorEl) errorEl.textContent = "";

    const participants = state.participants.map((value) => value.trim()).filter(Boolean);

    const reservations = loadReservations();
    const slot = getSlotById(state.selectedMeetingSlot, "MEETING");
    const room = MEETING_ROOMS.find((item) => item.id === state.selectedMeetingRoom);

    if (!slot || !room) return;

    const engine = new ReservationEngineClass(reservations, studentId);
    const validation = engine.validateMeeting({
      date: state.date,
      slot,
      roomId: state.selectedMeetingRoom,
      participants,
    });

    if (!validation.ok) {
      if (errorEl) errorEl.textContent = validation.message;
      return;
    }

    const newReservation = {
      id: generateReservationId("M"),
      studentId,
      spaceType: "MEETING",
      date: state.date,
      timeSlots: [{ ...slot }],
      roomId: room.id,
      roomName: room.name,
      participants: validation.participants || participants,
      createdAt: new Date().toISOString(),
    };

    reservations.push(newReservation);
    saveReservations(reservations);

    state.participants = ["", "", ""];
    renderMeetingTimeSlots();
    renderMeetingRooms();
    renderMeetingSummary();
    renderMyReservations();
    clearPendingReservation();
    postSaveAlert();
  }

  function renderReadingTimeSlots() {
    const grid = document.getElementById("reading-time-grid");
    if (!grid) return;

    const reservations = loadReservations();
    grid.innerHTML = "";

    const createSlotCard = (slot) => {
      const card = document.createElement("div");
      card.className = "slot-card";

      const title = document.createElement("strong");
      title.textContent = slot.label;

      const status = document.createElement("span");
      const available = isReadingSlotAvailable(reservations, slot);
      status.textContent = available ? "예약 가능" : "예약 불가";
      status.className = `status-pill ${available ? "status-available" : "status-blocked"}`;

      const button = document.createElement("button");
      button.type = "button";

      const selected = state.selectedReadingSlots.includes(slot.id);
      button.textContent = selected ? "선택 취소" : "예약 가능";

      if (!available) {
        button.textContent = "예약 불가";
        button.disabled = true;
        button.classList.add("blocked");
      } else if (!selected && !canSelectReadingSlot(slot)) {
        button.disabled = true;
        button.classList.add("blocked");
      } else {
        button.addEventListener("click", () => handleReadingSlotClick(slot));
      }

      if (selected) {
        card.classList.add("selected");
      }

      card.append(title, status, button);
      return card;
    };

    for (let i = 0; i < READING_SLOTS.length; i += 2) {
      const row = document.createElement("div");
      row.className = "slot-row";

      const firstSlot = READING_SLOTS[i];
      if (firstSlot) {
        row.appendChild(createSlotCard(firstSlot));
      }

      const secondSlot = READING_SLOTS[i + 1];
      if (secondSlot) {
        row.appendChild(createSlotCard(secondSlot));
      }

      grid.appendChild(row);
    }

    updateReadingProceedButton();
  }

  function handleReadingSlotClick(slot) {
    const alreadySelected = state.selectedReadingSlots.includes(slot.id);
    if (alreadySelected) {
      state.selectedReadingSlots = state.selectedReadingSlots.filter((id) => id !== slot.id);
    } else if (canSelectReadingSlot(slot)) {
      state.selectedReadingSlots.push(slot.id);
    }

    state.selectedSeat = null;
    renderReadingTimeSlots();
    updateReadingProceedButton();
  }

  function updateReadingProceedButton() {
    const proceedButton = document.getElementById("readingProceedBtn");
    if (!proceedButton) return;
    const enabled = state.spaceType === "READING" && state.selectedReadingSlots.length > 0;
    proceedButton.disabled = !enabled;
  }

  function renderSeatMap() {
    const map = document.getElementById("reading-seat-map");
    if (!map) return;

    if (state.selectedReadingSlots.length === 0) {
      map.innerHTML = "";
      toggleSection("reading-seat-section", false);
      return;
    }

    toggleSection("reading-seat-section", true);
    const reservations = loadReservations();
    const selectedSlots = state.selectedReadingSlots
      .map((id) => getSlotById(id, "READING"))
      .filter(Boolean);

    map.innerHTML = "";

    const seatsPerRow = 3;
    for (let i = 0; i < READING_SEATS.length; i += seatsPerRow) {
      const row = document.createElement("div");
      row.className = "seat-row";

      const rowSeats = READING_SEATS.slice(i, i + seatsPerRow);
      rowSeats.forEach((seat) => {
        const card = document.createElement("div");
        card.className = "seat-card";

        const label = document.createElement("strong");
        label.textContent = seat.label;

        const button = document.createElement("button");
        button.type = "button";

        const available = ReservationEngineClass.isSeatFree(reservations, state.date, seat.id, selectedSlots);
        const selected = state.selectedSeat === seat.id;

        if (!available) {
          button.textContent = "예약 불가";
          button.disabled = true;
          button.classList.add("blocked");
        } else {
          button.textContent = selected ? "선택됨" : "예약 가능";
          button.addEventListener("click", () => handleSeatSelection(seat.id));
        }

        if (selected) {
          button.classList.add("selected");
        }

        card.append(label, button);
        row.appendChild(card);
      });

      map.appendChild(row);
    }
  }

  function handleSeatSelection(seatId) {
    state.selectedSeat = state.selectedSeat === seatId ? null : seatId;
    renderSeatMap();
    renderReadingSummary();
    runAvailabilityFlow();
  }

  function handleRandomSeatAssignment() {
    if (state.spaceType !== "READING" || !state.date || state.selectedReadingSlots.length === 0) {
      alert("열람실 예약을 위해 먼저 날짜와 시간대를 선택해 주세요.");
      return;
    }

    const reservations = loadReservations();
    const selectedSlots = state.selectedReadingSlots
      .map((id) => getSlotById(id, "READING"))
      .filter(Boolean);

    const availableSeats = READING_SEATS.filter((seat) =>
      ReservationEngineClass.isSeatFree(reservations, state.date, seat.id, selectedSlots)
    ).map(
      (seat) => seat.id
    );

    if (availableSeats.length === 0) {
      alert("랜덤 배정 가능한 좌석이 없습니다.");
      return;
    }

    const randomIndex = Math.floor(Math.random() * availableSeats.length);
    state.selectedSeat = availableSeats[randomIndex];
    renderSeatMap();
    renderReadingSummary();
    runAvailabilityFlow();
  }

  function renderReadingSummary() {
    const summary = document.getElementById("reading-summary");
    if (!summary) return;

    if (state.selectedReadingSlots.length === 0 || !state.selectedSeat) {
      summary.innerHTML = "";
      toggleSection("reading-summary-section", false);
      return;
    }

    const slots = state.selectedReadingSlots
      .map((id) => getSlotById(id, "READING"))
      .filter(Boolean);

    const slotList = slots.map((slot) => `<li>${state.date} ${slot.label}</li>`).join("");

    const seatLabel = ReservationEngineClass.getSeatLabel
      ? ReservationEngineClass.getSeatLabel(state.selectedSeat)
      : state.selectedSeat;

    summary.innerHTML = `
      <p><strong>좌석</strong> : ${seatLabel}</p>
      <p><strong>선택한 시간</strong></p>
      <ul>${slotList}</ul>
      <p class="error" id="reading-error" aria-live="polite"></p>
      <button type="button" id="submitReadingReservation">예약 제출</button>
    `;
    toggleSection("reading-summary-section", true);
    scrollToSection("reading-summary-section");

    const submitButton = document.getElementById("submitReadingReservation");
    if (submitButton) {
      submitButton.addEventListener("click", () => handleReadingReservationSubmit(slots));
    }
  }

  function handleReadingReservationSubmit(slots) {
    const errorEl = document.getElementById("reading-error");
    if (errorEl) errorEl.textContent = "";

    const reservations = loadReservations();

    const engine = new ReservationEngineClass(reservations, studentId);
    const validation = engine.validateSeat({
      date: state.date,
      slots,
      seatId: state.selectedSeat,
    });

    if (!validation.ok) {
      if (errorEl) errorEl.textContent = validation.message;
      if (validation.code === "SEAT_BOOKED") {
        renderSeatMap();
      }
      return;
    }

    const newReservation = {
      id: generateReservationId("R"),
      studentId,
      spaceType: "READING",
      date: state.date,
      seatId: state.selectedSeat,
      seatLabel: getSeatLabel(state.selectedSeat),
      timeSlots: slots.map((slot) => ({ ...slot })),
      createdAt: new Date().toISOString(),
    };

    reservations.push(newReservation);
    saveReservations(reservations);

    renderReadingTimeSlots();
    renderSeatMap();
    renderReadingSummary();
    renderMyReservations();
    clearPendingReservation();
    postSaveAlert();
  }

  function renderMyReservations() {
    const listBody = document.getElementById("reservationList");
    if (!listBody) return;

    const emptyState = document.getElementById("reservation-empty");
    const reservations = loadReservations().filter((res) => res.studentId === studentId);

    reservations.sort((a, b) => {
      if (a.date === b.date) {
        return a.timeSlots[0].startMinutes - b.timeSlots[0].startMinutes;
      }
      return a.date.localeCompare(b.date);
    });

    listBody.innerHTML = "";

    if (reservations.length === 0) {
      if (emptyState) emptyState.classList.remove("hidden");
      return;
    }

    if (emptyState) emptyState.classList.add("hidden");

    reservations.forEach((reservation) => {
      const tr = document.createElement("tr");

      const slotText = reservation.timeSlots.map((slot) => slot.label).join(", ");
      const typeLabel = reservation.spaceType === "MEETING" ? "회의실" : "열람실";
      const seatLabel =
        ReservationEngineClass && ReservationEngineClass.getSeatLabel
          ? ReservationEngineClass.getSeatLabel(reservation.seatId)
          : reservation.seatId;
      const spaceLabel = reservation.spaceType === "MEETING" ? reservation.roomName : reservation.seatLabel || seatLabel;

      tr.innerHTML = `
        <td>${reservation.id}</td>
        <td>${typeLabel}</td>
        <td>${spaceLabel}</td>
        <td>${reservation.date}</td>
        <td>${slotText}</td>
      `;

      listBody.appendChild(tr);
    });
  }

  function toggleSection(id, show) {
    const section = document.getElementById(id);
    if (!section) return;
    section.classList.toggle("hidden", !show);
  }

  function scrollToSection(id) {
    const section = document.getElementById(id);
    if (!section || section.classList.contains("hidden")) return;
    section.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  function clearElement(id) {
    const el = document.getElementById(id);
    if (el) el.innerHTML = "";
  }

  function loadReservations() {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      return raw ? JSON.parse(raw) : [];
    } catch (err) {
      console.error("예약 데이터를 불러오지 못했습니다.", err);
      return [];
    }
  }

  function saveReservations(reservations) {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(reservations));
  }

  function setPendingReservation(data) {
    sessionStorage.setItem(PENDING_KEY, JSON.stringify(data));
  }

  function getPendingReservation() {
    try {
      const raw = sessionStorage.getItem(PENDING_KEY);
      return raw ? JSON.parse(raw) : null;
    } catch (err) {
      console.error("임시 예약 정보를 불러오지 못했습니다.", err);
      return null;
    }
  }

  function clearPendingReservation() {
    sessionStorage.removeItem(PENDING_KEY);
  }

  function generateReservationId(prefix) {
    return `${prefix}-${Date.now().toString(36)}`;
  }

  function getSlotById(id, type) {
    const list = type === "MEETING" ? MEETING_SLOTS : READING_SLOTS;
    return list.find((slot) => slot.id === id) || null;
  }

  function isMeetingSlotAvailable(reservations, slot) {
    return MEETING_ROOMS.some((room) => isRoomAvailable(reservations, state.date, room.id, slot.id));
  }

  function isRoomAvailable(reservations, date, roomId, slotId) {
    return !ReservationEngineClass.isRoomReserved(reservations, date, roomId, slotId);
  }

  function isReadingSlotAvailable(reservations, slot) {
    return READING_SEATS.some((seat) =>
      ReservationEngineClass.isSeatFree(reservations, state.date, seat.id, [slot])
    );
  }

  function canSelectReadingSlot(slot) {
    if (!state.spaceType || state.spaceType !== "READING") return false;
    if (state.selectedReadingSlots.includes(slot.id)) return true;
    if (state.selectedReadingSlots.length >= 2) return false;

    const conflicts = state.selectedReadingSlots
      .map((id) => getSlotById(id, "READING"))
      .filter(Boolean)
      .some((selectedSlot) => ReservationEngineClass.slotsOverlap(selectedSlot, slot));

    return !conflicts;
  }

  function postSaveAlert() {
    const goToMyReservation = window.confirm(
      "예약이 완료되었습니다.\n확인을 누르면 내 예약 관리 페이지로 이동합니다.\n취소를 누르면 예약을 이어서 진행할 수 있습니다."
    );

    if (goToMyReservation) {
      window.location.href = "my-reservations.html";
    } else {
      window.location.href = "search-availability.html";
    }
  }
})();
