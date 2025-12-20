// js/app.js
// Frontend orchestration for availability search and reservation flows.

(() => {
  let API = window.ApiClient;
  let apiClientLoader = null;
  const PENDING_KEY = "pendingReservation";

  const MEETING_ROOMS = [
    { id: 1, name: "회의실 1", capacity: 6 },
    { id: 2, name: "회의실 2", capacity: 8 },
    { id: 3, name: "회의실 3", capacity: 10 },
  ];

  const MEETING_SLOTS = createSlots({ startHour: 9, endHour: 18, duration: 1 });
  const READING_SLOTS = createSlots({ startHour: 9, endHour: 18, duration: 2 });

  const state = {
    studentId: null,
    filters: {
      spaceType: null,
      date: "",
    },
    meetingStatus: null,
    seatStatus: null,
    selectedReadingSlot: null,
    selectedSeat: null,
    selectedMeetingRoom: null,
    participants: ["", "", ""],
  };

  document.addEventListener("DOMContentLoaded", () => {
    state.studentId = sessionStorage.getItem("studentId");
    if (!state.studentId) {
      alert("로그인이 필요합니다.");
      window.location.href = "login.html";
      return;
    }

    renderUserSummary(state.studentId);
    bindLogout();

    initSearchPage();
    initMeetingReservationPage();
    initSeatReservationPage();
  });

  function createSlots({ startHour, endHour, duration }) {
    const slots = [];
    for (let hour = startHour; hour + duration <= endHour; hour += 1) {
      const startMinutes = hour * 60;
      const endMinutes = (hour + duration) * 60;
      const startLabel = `${formatHour(hour)}:00`;
      const endLabel = `${formatHour(hour + duration)}:00`;
      slots.push({
        id: `${hour}-${hour + duration}`,
        label: `${startLabel} ~ ${endLabel}`,
        startMinutes,
        endMinutes,
        start: startLabel,
        end: endLabel,
      });
    }
    return slots;
  }

  function formatHour(value) {
    return String(value).padStart(2, "0");
  }

  function parseDateOnly(dateStr) {
    if (!dateStr) return null;
    const [year, month, day] = dateStr.split("-").map(Number);
    if ([year, month, day].some((value) => Number.isNaN(value))) {
      return null;
    }
    return new Date(year, month - 1, day);
  }

  function isPastDate(dateStr) {
    const target = parseDateOnly(dateStr);
    if (!target) return false;
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    target.setHours(0, 0, 0, 0);
    return target < today;
  }

  function getSlotStartMinutes(slot) {
    if (!slot) return null;
    if (typeof slot.startMinutes === "number") return slot.startMinutes;
    if (typeof slot.start === "string") {
      const [hour, minute] = slot.start.split(":").map(Number);
      if (!Number.isNaN(hour) && !Number.isNaN(minute)) {
        return hour * 60 + minute;
      }
    }
    return null;
  }

  function isSlotInPast(dateStr, slot) {
    const target = parseDateOnly(dateStr);
    if (!target) return false;
    const startMinutes = getSlotStartMinutes(slot);
    if (startMinutes === null) return false;

    const today = new Date();
    const targetMidnight = new Date(target);
    targetMidnight.setHours(0, 0, 0, 0);
    const todayMidnight = new Date(today);
    todayMidnight.setHours(0, 0, 0, 0);

    if (targetMidnight < todayMidnight) return true;
    if (targetMidnight > todayMidnight) return false;

    const nowMinutes = today.getHours() * 60 + today.getMinutes();
    return startMinutes <= nowMinutes;
  }

  function updateDateValidation(dateValue) {
    const messageEl = document.getElementById("reservationDateMessage");
    if (!messageEl) return;
    if (!dateValue) {
      messageEl.textContent = "";
      messageEl.className = "notice";
      return;
    }

    if (isPastDate(dateValue)) {
      messageEl.textContent = "과거 날짜는 예약할 수 없습니다.";
      messageEl.className = "notice error";
      return;
    }

    messageEl.textContent = "예약 가능한 날짜입니다.";
    messageEl.className = "notice success";
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

  function initSearchPage() {
    const page = document.getElementById("search-page");
    if (!page) return;

    const dateInput = document.getElementById("reservationDate");
    const typeInputs = document.querySelectorAll('input[name="spaceType"]');
    const readingProceedBtn = document.getElementById("readingProceedBtn");

    typeInputs.forEach((input) => {
      input.addEventListener("change", () => {
        state.filters.spaceType = input.value;
        handleFilterChange();
      });
    });

    if (dateInput) {
      const handleDateChange = () => {
        const value = dateInput.value;
        updateDateValidation(value);
        state.filters.date = value;
        handleFilterChange();
      };

      dateInput.addEventListener("change", handleDateChange);
      dateInput.addEventListener("input", handleDateChange);
    }

    if (readingProceedBtn) {
      readingProceedBtn.addEventListener("click", () => {
        if (!state.selectedReadingSlot) return;
        const slot = getSlotById(state.selectedReadingSlot, "READING");
        if (!slot) return;
        setPendingReservation({
          type: "READING",
          date: state.filters.date,
          slot,
        });
        window.location.href = "seat-reservation.html";
      });
    }

    handleFilterChange();
  }

  async function handleFilterChange() {
    const date = state.filters.date;
    const type = state.filters.spaceType;
    state.selectedReadingSlot = null;
    state.selectedSeat = null;

    toggleSection("meeting-time-section", false);
    toggleSection("reading-time-section", false);

    if (!date || !type) {
      clearElement("meeting-time-list");
      clearElement("reading-time-grid");
      updateReadingProceedButton();
      return;
    }

    if (isPastDate(date)) {
      clearElement("meeting-time-list");
      clearElement("reading-time-grid");
      updateReadingProceedButton();
      return;
    }

    try {
      await ensureApiClient();
    } catch (error) {
      console.error(error);
      alert(error.message || "API 클라이언트를 불러오지 못했습니다.");
      return;
    }

    if (type === "MEETING") {
      await fetchMeetingStatus(date);
      renderMeetingTimeSlots();
      toggleSection("meeting-time-section", true);
    } else if (type === "READING") {
      await fetchSeatStatus(date);
      renderReadingTimeSlots();
      toggleSection("reading-time-section", true);
    }
  }

  async function fetchMeetingStatus(date) {
    await ensureApiClient().catch((error) => {
      console.error(error);
    });
    const listEl = document.getElementById("meeting-time-list");
    if (listEl) {
      listEl.innerHTML = "<p class=\"notice\">회의실 현황을 불러오는 중...</p>";
    }
    try {
      const data = await API.fetchMeetingRoomStatus(date);
      state.meetingStatus = data;
    } catch (error) {
      console.error(error);
      state.meetingStatus = null;
      if (listEl) {
        listEl.innerHTML = `<p class="error">${error.message || "회의실 현황을 불러오지 못했습니다."}</p>`;
      }
    }
  }

  async function fetchSeatStatus(date) {
    await ensureApiClient().catch((error) => {
      console.error(error);
    });
    const grid = document.getElementById("reading-time-grid");
    if (grid) {
      grid.innerHTML = "<p class=\"notice\">좌석 현황을 불러오는 중...</p>";
    }
    try {
      const data = await API.fetchSeatStatus(date);
      state.seatStatus = data;
    } catch (error) {
      console.error(error);
      state.seatStatus = null;
      if (grid) {
        grid.innerHTML = `<p class="error">${error.message || "좌석 현황을 불러오지 못했습니다."}</p>`;
      }
    }
  }

  function renderMeetingTimeSlots() {
    const listEl = document.getElementById("meeting-time-list");
    if (!listEl) return;

    if (!state.meetingStatus || !state.meetingStatus.rooms?.length) {
      listEl.innerHTML = "<p class=\"notice\">선택한 날짜의 회의실 정보를 찾을 수 없습니다.</p>";
      return;
    }

    const slotCount = state.meetingStatus.rooms[0].slots.length;
    listEl.innerHTML = "";
    let visibleCount = 0;

    for (let index = 0; index < slotCount; index += 1) {
      const slotMeta = state.meetingStatus.rooms[0].slots[index];
      const slot = getSlotMeta(slotMeta.start, slotMeta.end, "MEETING");
      if (!slot) continue;

      const availableRooms = state.meetingStatus.rooms.filter((room) => {
        const slotInfo = room.slots[index];
        return slotInfo && slotInfo.is_available;
      }).length;

      const isPast = isSlotInPast(state.filters.date, slot);
      if (!isPast && availableRooms === 0) {
        continue;
      }

      visibleCount += 1;

      const row = document.createElement("div");
      row.className = "time-slot-row";

      const label = document.createElement("strong");
      label.textContent = slot.label;

      const info = document.createElement("span");
      if (isPast) {
        info.className = "notice status-blocked";
        info.textContent = "지난 시간";
      } else {
        info.className = "notice";
        info.textContent = `예약 가능 회의실 ${availableRooms}개`;
      }

      const button = document.createElement("button");
      button.type = "button";
      if (isPast) {
        button.textContent = "지난 시간";
        button.disabled = true;
      } else {
        button.textContent = "회의실 선택";
        button.disabled = false;
        button.addEventListener("click", () => {
          setPendingReservation({
            type: "MEETING",
            date: state.filters.date,
            slot,
          });
          window.location.href = "meeting-room-reservation.html";
        });
      }

      row.append(label, info, button);
      listEl.appendChild(row);
    }

    if (visibleCount === 0) {
      listEl.innerHTML = "<p class=\"notice\">예약 가능한 시간이 없습니다.</p>";
    }
  }

  function renderReadingTimeSlots() {
    const grid = document.getElementById("reading-time-grid");
    if (!grid) return;

    if (!state.seatStatus || !state.seatStatus.seats?.length) {
      grid.innerHTML = "<p class=\"notice\">선택한 날짜의 좌석 정보를 찾을 수 없습니다.</p>";
      return;
    }

    grid.innerHTML = "";

    const visibleSlots = READING_SLOTS.filter((slot) => {
      if (isSlotInPast(state.filters.date, slot)) return true;
      return countAvailableSeatsForSlot(slot) > 0;
    });

    if (visibleSlots.length === 0) {
      grid.innerHTML = "<p class=\"notice\">예약 가능한 시간이 없습니다.</p>";
      state.selectedReadingSlot = null;
      updateReadingProceedButton();
      return;
    }

    if (state.selectedReadingSlot) {
      const selectedSlot = getSlotById(state.selectedReadingSlot, "READING");
      const stillVisible = visibleSlots.some((slot) => slot.id === state.selectedReadingSlot);
      if (!stillVisible || (selectedSlot && isSlotInPast(state.filters.date, selectedSlot))) {
        state.selectedReadingSlot = null;
      }
    }

    for (let i = 0; i < visibleSlots.length; i += 2) {
      const row = document.createElement("div");
      row.className = "slot-row";

      const firstSlot = visibleSlots[i];
      if (firstSlot) {
        row.appendChild(createSeatSlotCard(firstSlot));
      }

      const secondSlot = visibleSlots[i + 1];
      if (secondSlot) {
        row.appendChild(createSeatSlotCard(secondSlot));
      }

      grid.appendChild(row);
    }

    updateReadingProceedButton();
  }

  function createSeatSlotCard(slot) {
    const card = document.createElement("div");
    card.className = "slot-card";

    const title = document.createElement("strong");
    title.textContent = slot.label;

    const availableCount = countAvailableSeatsForSlot(slot);
    const isPast = isSlotInPast(state.filters.date, slot);
    const status = document.createElement("span");
    const isBlocked = isPast || availableCount === 0;
    status.className = `status-pill ${isBlocked ? "status-blocked" : "status-available"}`;
    if (isPast) {
      status.textContent = "지난 시간";
    } else {
      status.textContent = availableCount > 0 ? `${availableCount}석 예약 가능` : "예약 불가";
    }

    const button = document.createElement("button");
    button.type = "button";
    const selected = !isPast && state.selectedReadingSlot === slot.id;
    if (isPast) {
      button.textContent = "지난 시간";
    } else {
      button.textContent = selected ? "선택됨" : "예약 선택";
    }
    button.disabled = isBlocked;

    if (!isBlocked) {
      button.addEventListener("click", () => {
        if (state.selectedReadingSlot === slot.id) {
          state.selectedReadingSlot = null;
        } else {
          state.selectedReadingSlot = slot.id;
        }
        renderReadingTimeSlots();
      });
    } else {
      button.classList.add("blocked");
    }

    if (selected) {
      card.classList.add("selected");
    }

    card.append(title, status, button);
    return card;
  }

  function countAvailableSeatsForSlot(slot) {
    if (!state.seatStatus?.seats?.length) return 0;
    return state.seatStatus.seats.filter((seat) =>
      isSeatFree(seat, slot.start, slot.end)
    ).length;
  }

  function updateReadingProceedButton() {
    const proceedButton = document.getElementById("readingProceedBtn");
    if (!proceedButton) return;
    const enabled = state.filters.spaceType === "READING" && Boolean(state.selectedReadingSlot);
    proceedButton.disabled = !enabled;
  }

  function initMeetingReservationPage() {
    const page = document.getElementById("meeting-room-page");
    if (!page) return;

    const contextError = document.getElementById("meeting-context-error");
    const pending = getPendingReservation();
    state.selectedMeetingRoom = null;
    state.participants = ["", "", ""];

    if (!pending || pending.type !== "MEETING" || !pending.slot || !pending.date) {
      if (contextError) {
        contextError.classList.remove("hidden");
        contextError.textContent = "유효한 예약 정보가 없습니다. 다시 조건을 선택해 주세요.";
      }
      toggleSection("meeting-room-section", false);
      toggleSection("meeting-summary-section", false);
      return;
    }

    populateMeetingContext(pending);
    loadMeetingRoomOptions(pending);
  }

  async function loadMeetingRoomOptions(pending) {
    const listEl = document.getElementById("meeting-room-list");
    if (listEl) {
      listEl.innerHTML = "<p class=\"notice\">회의실 정보를 불러오는 중입니다...</p>";
    }
    try {
      await ensureApiClient();
      const status = await API.fetchMeetingRoomStatus(pending.date);
      state.meetingStatus = status;
      renderMeetingRooms(pending);
    } catch (error) {
      console.error(error);
      if (listEl) {
        listEl.innerHTML = `<p class="error">${error.message || "회의실 정보를 불러오지 못했습니다."}</p>`;
      }
    }
  }

  function populateMeetingContext(pending) {
    const dateEl = document.getElementById("meeting-context-date");
    const slotEl = document.getElementById("meeting-context-slot");
    if (dateEl) dateEl.textContent = `예약 날짜: ${pending.date}`;
    if (slotEl) slotEl.textContent = `예약 시간: ${pending.slot?.label}`;
  }

  function renderMeetingRooms(pending) {
    const section = document.getElementById("meeting-room-section");
    const listEl = document.getElementById("meeting-room-list");
    if (!section || !listEl) return;

    if (!state.meetingStatus) {
      section.classList.add("hidden");
      return;
    }

    const slotIndex = getMeetingSlotIndex(pending.slot);
    if (slotIndex < 0) {
      listEl.innerHTML = "<p class=\"error\">선택한 시간 정보를 찾을 수 없습니다.</p>";
      return;
    }

    section.classList.remove("hidden");
    listEl.innerHTML = "";

    MEETING_ROOMS.forEach((room) => {
      const card = document.createElement("div");
      card.className = "room-card";

      const info = document.createElement("div");
      info.innerHTML = `<strong>${room.name}</strong><p class="notice">수용 인원 ${room.capacity}명</p>`;

      const button = document.createElement("button");
      button.type = "button";

      const slotInfo = state.meetingStatus.rooms.find((item) => item.room_id === room.id)?.slots?.[slotIndex];
      const available = slotInfo?.is_available;
      const selected = state.selectedMeetingRoom === room.id;

      if (!available) {
        button.textContent = "예약 불가";
        button.disabled = true;
        button.classList.add("blocked");
      } else {
        button.textContent = selected ? "선택됨" : "예약 가능";
        button.addEventListener("click", () => {
          state.selectedMeetingRoom = room.id;
          renderMeetingRooms(pending);
          renderMeetingSummary(pending);
        });
      }

      if (selected) {
        card.classList.add("selected");
      }

      card.append(info, button);
      listEl.appendChild(card);
    });

    renderMeetingSummary(pending);
  }

  function renderMeetingSummary(pending) {
    const section = document.getElementById("meeting-summary-section");
    const container = document.getElementById("meeting-summary");
    if (!section || !container) return;

    if (!state.selectedMeetingRoom) {
      section.classList.add("hidden");
      container.innerHTML = "";
      return;
    }

    const room = MEETING_ROOMS.find((item) => item.id === state.selectedMeetingRoom);
    const participantFields = state.participants
      .map(
        (value, index) => `
          <div class="participant-row">
            <label for="participant-${index}">참여자 ${index + 1}</label>
            <input
              type="text"
              id="participant-${index}"
              data-participant-index="${index}"
              placeholder="20230000${index + 1}"
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

    container.innerHTML = `
      <p><strong>공간</strong> : ${room?.name || `회의실 ${state.selectedMeetingRoom}`}</p>
      <p><strong>일시</strong> : ${pending.date} ${pending.slot.label}</p>
      <div id="participantInputGroup">
        <p><strong>참여자 목록</strong> (최소 3명, 학번 9자리)</p>
        ${participantFields}
        <button type="button" id="addParticipantBtn" class="secondary-button">참여자 추가</button>
      </div>
      <p class="error" id="meeting-error" aria-live="polite"></p>
      <button type="button" id="submitMeetingReservation">예약 제출</button>
    `;

    section.classList.remove("hidden");
    scrollToSection("meeting-summary-section");

    const participantInputs = container.querySelectorAll("input[data-participant-index]");
    participantInputs.forEach((input) => {
      input.addEventListener("input", (event) => {
        const target = event.target;
        const index = Number(target.dataset.participantIndex);
        if (Number.isNaN(index)) return;
        state.participants[index] = target.value.trim();
      });
    });

    const addButton = document.getElementById("addParticipantBtn");
    if (addButton) {
      addButton.addEventListener("click", () => {
        if (state.participants.length >= 6) {
          alert("참여자는 최대 6명까지 입력할 수 있습니다.");
          return;
        }
        state.participants.push("");
        renderMeetingSummary(pending);
      });
    }

    const submitButton = document.getElementById("submitMeetingReservation");
    if (submitButton) {
      submitButton.addEventListener("click", () => handleMeetingReservationSubmit(pending));
    }
  }

  async function handleMeetingReservationSubmit(pending) {
    const errorEl = document.getElementById("meeting-error");
    if (errorEl) errorEl.textContent = "";

    const participants = state.participants.map((value) => value.trim()).filter(Boolean);

    if (participants.length < 3) {
      if (errorEl) errorEl.textContent = "참여자는 최소 3명 이상 입력해야 합니다.";
      return;
    }

    if (participants.some((id) => !/^\d{9}$/.test(id))) {
      if (errorEl) errorEl.textContent = "참여자 학번은 9자리 숫자여야 합니다.";
      return;
    }

    if (!state.selectedMeetingRoom) {
      if (errorEl) errorEl.textContent = "회의실을 먼저 선택해 주세요.";
      return;
    }

    try {
      await ensureApiClient();
      await API.createMeetingReservation({
        room_id: state.selectedMeetingRoom,
        date: pending.date,
        start_time: pending.slot.start,
        end_time: pending.slot.end,
        participants: participants.map((studentId) => ({ student_id: studentId })),
      });
      clearPendingReservation();
      alert("회의실 예약이 완료되었습니다.");
      postReservationRedirect();
    } catch (apiError) {
      console.error(apiError);
      if (errorEl) {
        errorEl.textContent = apiError.message || "예약을 생성하지 못했습니다.";
      } else {
        alert(apiError.message || "예약을 생성하지 못했습니다.");
      }
    }
  }

  function initSeatReservationPage() {
    const page = document.getElementById("seat-reservation-page");
    if (!page) return;

    const contextError = document.getElementById("reading-context-error");
    const pending = getPendingReservation();
    state.selectedSeat = null;

    if (!pending || pending.type !== "READING" || !pending.slot || !pending.date) {
      if (contextError) {
        contextError.classList.remove("hidden");
        contextError.textContent = "유효한 예약 정보가 없습니다. 다시 조건을 선택해 주세요.";
      }
      toggleSection("reading-seat-section", false);
      toggleSection("reading-summary-section", false);
      return;
    }

    populateSeatContext(pending);
    loadSeatOptions(pending);

    const randomSeatBtn = document.getElementById("randomSeatBtn");
    if (randomSeatBtn) {
      randomSeatBtn.addEventListener("click", () => handleRandomSeatReservation(pending));
    }
  }

  function populateSeatContext(pending) {
    const listEl = document.getElementById("reading-context-slots");
    if (!listEl) return;
    listEl.innerHTML = `<li>${pending.date} ${pending.slot.label}</li>`;
  }

  async function loadSeatOptions(pending) {
    const map = document.getElementById("reading-seat-map");
    if (map) {
      map.innerHTML = "<p class=\"notice\">좌석 지도를 불러오는 중입니다...</p>";
    }
    try {
      await ensureApiClient();
      const status = await API.fetchSeatStatus(pending.date);
      state.seatStatus = status;
      renderSeatMap(pending);
    } catch (error) {
      console.error(error);
      if (map) {
        map.innerHTML = `<p class="error">${error.message || "좌석 지도를 불러오지 못했습니다."}</p>`;
      }
    }
  }

  function renderSeatMap(pending) {
    const section = document.getElementById("reading-seat-section");
    const map = document.getElementById("reading-seat-map");
    if (!section || !map) return;

    if (!state.seatStatus) {
      section.classList.add("hidden");
      return;
    }

    section.classList.remove("hidden");
    map.innerHTML = "";

    const seats = state.seatStatus.seats || [];
    const seatsPerRow = 5;
    const rowsNeeded = Math.ceil(seats.length / seatsPerRow);

    for (let rowIndex = 0; rowIndex < rowsNeeded; rowIndex += 1) {
      const row = document.createElement("div");
      row.className = "seat-row";
      map.appendChild(row);
    }

    const rows = map.querySelectorAll(".seat-row");
    seats.forEach((seat, index) => {
      const rowIndex = Math.floor(index / seatsPerRow);
      const row = rows[rowIndex];
      if (!row) return;

      const card = document.createElement("div");
      card.className = "seat-card";

      const label = document.createElement("strong");
      label.textContent = `좌석 ${seat.seat_id}`;

      const button = document.createElement("button");
      button.type = "button";
      const available = isSeatFree(seat, pending.slot.start, pending.slot.end);
      const isSelectedSeat = state.selectedSeat === seat.seat_id;
      const selected = isSelectedSeat && available;

      if (!available) {
        button.textContent = "예약 불가";
        button.disabled = true;
        button.classList.add("blocked");
        if (isSelectedSeat) {
          state.selectedSeat = null;
        }
      } else {
        button.textContent = selected ? "선택됨" : "예약 가능";
        button.addEventListener("click", () => {
          state.selectedSeat = selected ? null : seat.seat_id;
          renderSeatMap(pending);
        });
      }

      if (selected) {
        card.classList.add("selected");
      }

      card.append(label, button);
      row.appendChild(card);
    });

    renderSeatSummary(pending);
  }

  function renderSeatSummary(pending) {
    const section = document.getElementById("reading-summary-section");
    const container = document.getElementById("reading-summary");
    if (!section || !container) return;

    if (!state.selectedSeat) {
      section.classList.add("hidden");
      container.innerHTML = "";
      return;
    }

    container.innerHTML = `
      <p><strong>좌석</strong> : 좌석 ${state.selectedSeat}</p>
      <p><strong>선택한 시간</strong></p>
      <ul><li>${pending.date} ${pending.slot.label}</li></ul>
      <p class="error" id="reading-error" aria-live="polite"></p>
      <button type="button" id="submitReadingReservation">예약 제출</button>
    `;

    section.classList.remove("hidden");
    scrollToSection("reading-summary-section");

    const submitButton = document.getElementById("submitReadingReservation");
    if (submitButton) {
      submitButton.addEventListener("click", () => handleSeatReservationSubmit(pending));
    }
  }

  async function handleSeatReservationSubmit(pending) {
    const errorEl = document.getElementById("reading-error");
    if (errorEl) errorEl.textContent = "";

    if (!state.selectedSeat) {
      if (errorEl) errorEl.textContent = "좌석을 먼저 선택해 주세요.";
      return;
    }

    try {
      await ensureApiClient();
      await API.createSeatReservation(
        {
          date: pending.date,
          start_time: pending.slot.start,
          end_time: pending.slot.end,
          seat_id: state.selectedSeat,
        },
        { random: false }
      );
      clearPendingReservation();
      alert(`좌석 ${state.selectedSeat} 예약이 완료되었습니다.`);
      postReservationRedirect();
    } catch (apiError) {
      console.error(apiError);
      if (errorEl) {
        errorEl.textContent = apiError.message || "좌석 예약을 생성하지 못했습니다.";
      } else {
        alert(apiError.message || "좌석 예약을 생성하지 못했습니다.");
      }
    }
  }

  async function handleRandomSeatReservation(pending) {
    const errorEl = document.getElementById("reading-error");
    if (errorEl) errorEl.textContent = "";

    try {
      await ensureApiClient();
      const payload = await API.createSeatReservation(
        {
          date: pending.date,
          start_time: pending.slot.start,
          end_time: pending.slot.end,
        },
        { random: true }
      );
      clearPendingReservation();
      alert(`랜덤 좌석 배정 완료! 좌석 ${payload?.seat_id ?? ""}이(가) 예약되었습니다.`);
      postReservationRedirect();
    } catch (apiError) {
      console.error(apiError);
      if (errorEl) {
        errorEl.textContent = apiError.message || "랜덤 좌석 배정에 실패했습니다.";
      } else {
        alert(apiError.message || "랜덤 좌석 배정에 실패했습니다.");
      }
    }
  }

  function isSeatFree(seatStatus, start, end) {
    const slot = seatStatus.slots.find((item) => item.start === start && item.end === end);
    return slot ? slot.is_available : false;
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

  function setPendingReservation(data) {
    sessionStorage.setItem(PENDING_KEY, JSON.stringify(data));
  }

  function getPendingReservation() {
    try {
      const raw = sessionStorage.getItem(PENDING_KEY);
      const data = raw ? JSON.parse(raw) : null;
      return normalizePendingReservation(data);
    } catch (err) {
      console.error("임시 예약 정보를 불러오지 못했습니다.", err);
      return null;
    }
  }

  function clearPendingReservation() {
    sessionStorage.removeItem(PENDING_KEY);
  }

  function postReservationRedirect() {
    const goToMyReservation = window.confirm(
      "예약이 완료되었습니다.\n확인을 누르면 내 예약 관리 페이지로 이동합니다.\n취소를 누르면 예약 가능 시간 조회 페이지로 이동합니다."
    );

    if (goToMyReservation) {
      window.location.href = "my-reservations.html";
    } else {
      window.location.href = "search-availability.html";
    }
  }

  function getSlotById(id, type) {
    const list = type === "MEETING" ? MEETING_SLOTS : READING_SLOTS;
    return list.find((slot) => slot.id === id) || null;
  }

  function getSlotMeta(start, end, type) {
    const list = type === "MEETING" ? MEETING_SLOTS : READING_SLOTS;
    return list.find((slot) => slot.start === start && slot.end === end) || null;
  }

  function getMeetingSlotIndex(slot) {
    if (!slot || !state.meetingStatus?.rooms?.length) return -1;
    const referenceRoom = state.meetingStatus.rooms[0];
    return referenceRoom.slots.findIndex(
      (item) => item.start === slot.start && item.end === slot.end
    );
  }

  function normalizePendingReservation(pending) {
    if (!pending) return null;
    const normalized = { ...pending };

    if (normalized.type === "MEETING" && !normalized.slot) {
      if (normalized.slotId) {
        normalized.slot = getSlotById(normalized.slotId, "MEETING");
      }
    }

    if (normalized.type === "READING" && !normalized.slot) {
      let slotId = null;
      if (Array.isArray(normalized.slotIds) && normalized.slotIds.length > 0) {
        slotId = normalized.slotIds[0];
      } else if (normalized.slotId) {
        slotId = normalized.slotId;
      }

      if (slotId) {
        normalized.slot = getSlotById(slotId, "READING");
      }
    }

    return normalized;
  }

  function ensureApiClient() {
    if (API) {
      return Promise.resolve(API);
    }

    if (apiClientLoader) {
      return apiClientLoader;
    }

    apiClientLoader = new Promise((resolve, reject) => {
      const script = document.createElement("script");
      script.src = "js/api-client.js";
      script.async = true;
      script.onload = () => {
        API = window.ApiClient;
        if (API) {
          resolve(API);
        } else {
          reject(new Error("API 클라이언트를 초기화하지 못했습니다."));
        }
      };
      script.onerror = () => reject(new Error("API 스크립트를 불러오지 못했습니다."));
      document.head.appendChild(script);
    });

    return apiClientLoader;
  }
})();
