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
let chatSession = {};

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

function addSlotSuggestions(suggestedSlots) {
  if (!suggestedSlots?.length) {
    return;
  }

  const wrapper = document.createElement("div");
  wrapper.className = "suggested-slots";

  suggestedSlots.forEach((slot) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "suggested-slot";
    button.textContent = `#${slot.id} ${slot.city} · ${slot.test_type} · ${formatDate(slot.test_date)} ${formatTime(slot.test_time)}`;
    button.addEventListener("click", () => selectSlot(slot, true));
    wrapper.appendChild(button);
  });

  messages.appendChild(wrapper);
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
          <span class="pill">Slot #${slot.id}</span>
          <span class="pill">${slot.test_type}</span>
          <span class="pill">${formatDate(slot.test_date)}</span>
          <span class="pill">${formatTime(slot.test_time)}</span>
          <span class="pill">${slot.available_seats} seats</span>
        </div>
      </div>
      <button class="book-button" type="button" ${slot.available_seats <= 0 ? "disabled" : ""}>
        ${slot.available_seats <= 0 ? "Full" : "Chat book"}
      </button>
    `;

    card.querySelector("button").addEventListener("click", () => selectSlot(slot, true));
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

function updateSelectedSlot() {
  if (!selectedSlot) {
    selectedSlotBox.textContent = "Ask for available slots or select one from the list.";
    return;
  }

  selectedSlotBox.textContent = `${selectedSlot.city}, ${selectedSlot.test_center_name} · Slot #${selectedSlot.id} · ${selectedSlot.test_type} · ${formatDate(selectedSlot.test_date)} at ${formatTime(selectedSlot.test_time)}`;
}

function resetConversation() {
  chatSession = {};
  selectedSlot = null;
  messages.innerHTML = "";
  chatInput.disabled = false;
  sendButton.disabled = false;
  chatInput.placeholder = "Ask: show Chennai slots, or book slot #1...";
  updateSelectedSlot();
  addMessage("Hi. I can search IELTS slots and book one through the MCP booking tools. Try “show available slots in Chennai” or pick a slot card.");
}

function selectSlot(slot, announce = false) {
  selectedSlot = slot;
  chatSession.slot_id = slot.id;
  updateSelectedSlot();
  renderSlots();

  if (announce) {
    addMessage(`Selected slot #${slot.id}. Send your name, email, phone, and passport number when you are ready to book.`);
  }

  document.querySelector("#booking-chat").scrollIntoView({ behavior: "smooth", block: "start" });
  chatInput.focus();
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

async function sendChatMessage(text) {
  chatInput.disabled = true;
  sendButton.disabled = true;

  try {
    const response = await fetch("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message: text,
        session: chatSession,
        selected_slot_id: selectedSlot?.id || null,
      }),
    });

    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.detail || "Chat request failed");
    }

    chatSession = payload.session || {};
    addMessage(payload.reply, "bot", payload.booking ? "success" : "");
    addSlotSuggestions(payload.slots);

    if (payload.booking) {
      await loadSlots();
    }
  } catch (error) {
    addMessage(`${error.message}. Check that the API, database, and local model settings are running.`);
  } finally {
    chatInput.disabled = false;
    sendButton.disabled = false;
    chatInput.focus();
  }
}

chatForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const text = chatInput.value.trim();

  if (!text) {
    return;
  }

  addMessage(text, "user");
  chatInput.value = "";
  await sendChatMessage(text);
});

cityFilter.addEventListener("change", renderSlots);
typeFilter.addEventListener("change", renderSlots);
refreshSlots.addEventListener("click", loadSlots);
resetChat.addEventListener("click", resetConversation);

resetConversation();
loadSlots();
