// Extract CSRF token
const csrfToken = document.querySelector('#csrf-form input[name="csrfmiddlewaretoken"]').value;

const chatBox = document.getElementById("chatbox");
const userInput = document.getElementById("userInput");
const sendBtn = document.getElementById("sendBtn");

// ✅ Format bot messages (supports **bold**, *italics*, line breaks)
function formatMessage(text) {
  return text
    .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
    .replace(/\*(.*?)\*/g, "<em>$1</em>")
    .replace(/\n/g, "<br>");
}

// --- 💾 Local Storage Chat Persistence ---
const CHAT_KEY = "healthmate_chat_history";

// Save chat messages to localStorage
function saveChatHistory() {
  const messages = Array.from(chatBox.children).map(el => ({
    type: el.classList.contains("user-message") ? "user" : "bot",
    html: el.innerHTML
  }));
  localStorage.setItem(CHAT_KEY, JSON.stringify(messages));
}

// Load chat messages from localStorage
function loadChatHistory() {
  const saved = localStorage.getItem(CHAT_KEY);
  if (saved) {
    const messages = JSON.parse(saved);
    messages.forEach(msg => {
      const msgDiv = document.createElement("div");
      msgDiv.classList.add(msg.type === "user" ? "user-message" : "bot-message");
      msgDiv.innerHTML = msg.html;
      chatBox.appendChild(msgDiv);
    });
    chatBox.scrollTop = chatBox.scrollHeight;
  }
}

// Clear chat history (optional helper, can link to a “Clear Chat” button)
function clearChatHistory() {
  localStorage.removeItem(CHAT_KEY);
  chatBox.innerHTML = `
    <div class="bot-message">
      Hi there! 👋 I'm your health assistant.<br>
      I already know your profile details, so just ask about your meals, fitness, or any health concern.
    </div>
  `;
  saveChatHistory();
}

// --- 🧠 Chat Logic ---
async function sendMessage() {
  const message = userInput.value.trim();
  if (!message) return;

  // Add user message
  const userMsg = document.createElement("div");
  userMsg.classList.add("user-message");
  userMsg.textContent = message;
  chatBox.appendChild(userMsg);

  // Add placeholder bot message
  const botMsg = document.createElement("div");
  botMsg.classList.add("bot-message");
  botMsg.textContent = "Thinking...";
  chatBox.appendChild(botMsg);

  userInput.value = "";
  chatBox.scrollTop = chatBox.scrollHeight;

  saveChatHistory(); // 💾 Save after sending user message

  try {
    const response = await fetch("/api/health/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": csrfToken,
      },
      body: JSON.stringify({ message }),
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    const data = await response.json();
    const reply = data.reply || "Sorry, I couldn’t process that.";

    // Render formatted reply safely
    botMsg.innerHTML = formatMessage(reply);

  } catch (error) {
    console.error("Chat error:", error);
    botMsg.textContent = "Error connecting to AI.";
  }

  chatBox.scrollTop = chatBox.scrollHeight;
  saveChatHistory(); // 💾 Save after receiving bot reply
}

sendBtn.addEventListener("click", sendMessage);
userInput.addEventListener("keypress", (e) => {
  if (e.key === "Enter") sendMessage();
});

// --- 🔹 Modal Logic (unchanged) ---
const openRecordsBtn = document.getElementById("openRecordsBtn");
const recordsModal = document.getElementById("recordsModal");
const closeModal = document.getElementById("closeModal");

openRecordsBtn.addEventListener("click", () => {
  recordsModal.style.display = "block";
  setTimeout(() => recordsModal.classList.add("show"), 10);
});

closeModal.addEventListener("click", () => {
  recordsModal.classList.remove("show");
  setTimeout(() => {
    recordsModal.style.display = "none";
    const iframe = document.querySelector(".records-frame");
    iframe.src = iframe.src;
  }, 200);
});

window.addEventListener("message", (event) => {
  if (event.data.action === "closeRecordsModal") {
    recordsModal.classList.remove("show");
    setTimeout(() => {
      recordsModal.style.display = "none";
      const iframe = document.querySelector(".records-frame");
      iframe.src = iframe.src;
    }, 200);
  }
});

// --- 🔄 Load chat history when page loads ---
window.addEventListener("DOMContentLoaded", loadChatHistory);
