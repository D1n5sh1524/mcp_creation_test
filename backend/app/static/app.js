const slotList = document.querySelector("#slotList");
const cityFilter = document.querySelector("#cityFilter");
const typeFilter = document.querySelector("#typeFilter");
const refreshSlots = document.querySelector("#refreshSlots");
const selectedSlotBox = document.querySelector("#selectedSlot");
const messages = document.querySelector("#messages");
const chatForm = document.querySelector("#chatForm");
const chatInput = document.querySelector("#chatInput");
const sendButton = document.querySelector("#sendButton");
const resetChat = document.querySelector("#resetChat");

let slots = [];
let selectedSlot = null;
let bookingDraft = {};
let stepIndex = 0;

const steps = [
  {
    key: "first_name",
    prompt: "Great choice. What is your first name?",
    placeholder: "First name",
    validate: (value) => value.trim().length >= 2,
    error: "Please enter at least 2 characters for your first name.",
  },
  {
    key: "last_name",
    prompt: "Thanks. What is your last name?",
    placeholder: "Last name",
    validate: (value) => value.trim().length >= 2,
    error: "Please enter at least 2 characters for your last name.",
  },
  {
    key: "email",
    prompt: "What email should we use for the booking?",
    placeholder: "you@example.com",
    validate: (value) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value.trim()),
    error: "Please enter a valid email address.",
  },
  {
    key: "phone",
    prompt: "What phone number should we attach to the booking?",
    placeholder: "Phone number",
    validate: (value) => value.trim().replace(/\D/g, "").length >= 7,
    error: "Please enter a valid phone number.",
  },
  {
    key: "passport_number",
    prompt: "Last step: what is your passport number?",
    placeholder: "Passport number",
    validate: (value) => value.trim().length >= 5,
    error: "Please enter a valid passport number.",
  },
];

function formatDate(value) {
  return new Intl.DateTimeFormat("en", {
    weekday: "short",
    month: "short",
    day: "numeric",
    year: "numeric",
  }).format(new Date(`${value}T00:00:00`));
}

function formatTime(value) {
  return value.slice(0, 5);
}

function addMessage(text, sender = "bot", tone = "") {
  const message = document.createElement("div");
  message.className = `message ${sender} ${tone}`.trim();
  message.textContent = text;
  messages.appendChild(message);
  messages.scrollTop = messages.scrollHeight;
}

function filteredSlots() {
  return slots.filter((slot) => {
    const cityMatches = !cityFilter.value || slot.city === cityFilter.value;
    const typeMatches = !typeFilter.value || slot.test_type === typeFilter.value;
    return cityMatches && typeMatches;
  });
}

function renderSlots() {
  const visibleSlots = filteredSlots();
  slotList.innerHTML = "";

  if (!visibleSlots.length) {
    slotList.innerHTML = '<div class="empty-state">No slots match the current filters.</div>';
    return;
  }

  visibleSlots.forEach((slot) => {
    const card = document.createElement("article");
    card.className = `slot-card ${selectedSlot?.id === slot.id ? "is-selected" : ""}`;

    card.innerHTML = `
      <div>
        <h3>${slot.city} · ${slot.test_center_name}</h3>
        <div class="slot-meta">
          <span class="pill">${slot.test_type}</span>
          <span class="pill">${formatDate(slot.test_date)}</span>
          <span class="pill">${formatTime(slot.test_time)}</span>
          <span class="pill">${slot.available_seats} seats</span>
        </div>
      </div>
      <button class="book-button" type="button" ${slot.available_seats <= 0 ? "disabled" : ""}>
        ${slot.available_seats <= 0 ? "Full" : "Book"}
      </button>
    `;

    card.querySelector("button").addEventListener("click", () => selectSlot(slot));
    slotList.appendChild(card);
  });
}

function renderCities() {
  const cities = [...new Set(slots.map((slot) => slot.city))].sort();
  const currentValue = cityFilter.value;
  cityFilter.innerHTML = '<option value="">All cities</option>';

  cities.forEach((city) => {
    const option = document.createElement("option");
    option.value = city;
    option.textContent = city;
    cityFilter.appendChild(option);
  });

  cityFilter.value = cities.includes(currentValue) ? currentValue : "";
}

function resetConversation(keepSlot = true) {
  bookingDraft = {};
  stepIndex = 0;
  messages.innerHTML = "";

  if (!keepSlot) {
    selectedSlot = null;
  }

  if (!selectedSlot) {
    selectedSlotBox.textContent = "Select a slot to begin.";
    chatInput.placeholder = "Choose a slot first";
    chatInput.disabled = true;
    sendButton.disabled = true;
    addMessage("Pick any available test slot and I will guide you through the booking.");
    return;
  }

  selectedSlotBox.textContent = `${selectedSlot.city}, ${selectedSlot.test_center_name} · ${selectedSlot.test_type} · ${formatDate(selectedSlot.test_date)} at ${formatTime(selectedSlot.test_time)}`;
  chatInput.disabled = false;
  sendButton.disabled = false;
  chatInput.placeholder = steps[0].placeholder;
  addMessage(steps[0].prompt);
  chatInput.focus();
}

function selectSlot(slot) {
  selectedSlot = slot;
  renderSlots();
  resetConversation(true);
  document.querySelector("#booking-chat").scrollIntoView({ behavior: "smooth", block: "start" });
}

async function loadSlots() {
  slotList.innerHTML = '<div class="empty-state">Loading slots...</div>';

  try {
    const response = await fetch("/test-slots");
    if (!response.ok) {
      throw new Error("Could not load slots");
    }

    slots = await response.json();
    renderCities();
    renderSlots();
  } catch (error) {
    slotList.innerHTML = '<div class="empty-state">Slot loading failed. Make sure the API and database are running.</div>';
  }
}

async function submitBooking() {
  chatInput.disabled = true;
  sendButton.disabled = true;
  addMessage("Creating your booking now...");

  try {
    const response = await fetch("/bookings", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        slot_id: selectedSlot.id,
        candidate: bookingDraft,
      }),
    });

    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.detail || "Booking failed");
    }

    addMessage(
      `Booked. Your reference is ${payload.booking.booking_reference}. Remaining seats for this slot: ${payload.slot_remaining_seats}.`,
      "bot",
      "success",
    );
    await loadSlots();
  } catch (error) {
    addMessage(`${error.message}. You can reset the chat and try again.`);
  }
}

chatForm.addEventListener("submit", async (event) => {
  event.preventDefault();

  if (!selectedSlot || stepIndex >= steps.length) {
    return;
  }

  const step = steps[stepIndex];
  const value = chatInput.value.trim();

  if (!step.validate(value)) {
    addMessage(step.error);
    return;
  }

  bookingDraft[step.key] = value;
  addMessage(value, "user");
  chatInput.value = "";
  stepIndex += 1;

  if (stepIndex >= steps.length) {
    await submitBooking();
    return;
  }

  chatInput.placeholder = steps[stepIndex].placeholder;
  addMessage(steps[stepIndex].prompt);
});

cityFilter.addEventListener("change", renderSlots);
typeFilter.addEventListener("change", renderSlots);
refreshSlots.addEventListener("click", loadSlots);
resetChat.addEventListener("click", () => resetConversation(Boolean(selectedSlot)));

resetConversation(false);
loadSlots();
