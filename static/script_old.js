// ---------- Elements ----------
const chatBubble    = document.getElementById("chat-bubble");
const chatWindow    = document.getElementById("chat-window");
const chatClose     = document.getElementById("chat-close");
const sendBtn       = document.getElementById("send-btn");
const userInput     = document.getElementById("user-input");
const chatMessages  = document.getElementById("chat-messages");

// Add aria-live to messages for screen readers
if (chatMessages) {
  chatMessages.setAttribute("role", "status");
  chatMessages.setAttribute("aria-live", "polite");
  chatMessages.setAttribute("aria-atomic", "false");
}

// ---------- Open / Close ----------
function openChat() {
  chatWindow.classList.add("show");
  chatBubble.style.display = "none";
  try { localStorage.setItem("chat_open", "1"); } catch {}
  // focus the input after opening
  setTimeout(() => userInput && userInput.focus(), 120);
}
function closeChat() {
  chatWindow.classList.remove("show");
  chatBubble.style.display = "flex";
  try { localStorage.setItem("chat_open", "0"); } catch {}
  // return visual focus to bubble
  chatBubble && chatBubble.focus && chatBubble.focus();
}
chatBubble?.addEventListener("click", openChat);
chatClose?.addEventListener("click", closeChat);

// Close on ESC
document.addEventListener("keydown", (e) => {
  if (e.key === "Escape" && chatWindow.classList.contains("show")) {
    closeChat();
  }
});

// Close when clicking outside the chat window (but not on bubble)
document.addEventListener("click", (e) => {
  if (!chatWindow.classList.contains("show")) return;
  const within = chatWindow.contains(e.target) || chatBubble.contains(e.target);
  if (!within) closeChat();
});

// Restore last open state
(function restoreOpenState(){
  try {
    if (localStorage.getItem("chat_open") === "1") {
      openChat();
    }
  } catch {}
})();

// ---------- Send message (loading + guard) ----------
let sending = false;
function setLoading(isLoading){
  sending = isLoading;
  if (!sendBtn) return;
  sendBtn.disabled = isLoading;
  sendBtn.textContent = isLoading ? "…" : "Send";
}

async function sendMessage() {
  if (sending) return; // guard double submit
  const text = (userInput?.value || "").trim();
  if (!text) return;

  addMessage("user", text);
  if (userInput) userInput.value = "";
  setLoading(true);

  try{
    const res = await fetch("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text })
    });

    let data = {};
    try { data = await res.json(); } catch {}

    if (!res.ok) {
      addMessage("bot", data?.error || `Server error (${res.status})`);
    } else {
      addMessage("bot", data?.reply || "No reply");
    }
  } catch(e){
    addMessage("bot", "Network error. Please try again.");
  } finally {
    setLoading(false);
    userInput && userInput.focus();
  }
}

sendBtn?.addEventListener("click", sendMessage);
userInput?.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
});

// ---------- Message rendering ----------
function addMessage(role, text) {
  if (!chatMessages) return;
  const msg = document.createElement("div");
  msg.className = "message " + role;
  msg.textContent = text;
  chatMessages.appendChild(msg);
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

// ---------- Mobile viewport + orientation hint ----------
function setVH() {
  const vh = window.innerHeight * 0.01;
  document.documentElement.style.setProperty("--vh", `${vh}px`);
}
window.addEventListener("load", setVH);
window.addEventListener("resize", setVH);

let orientationBanner;
function showOrientationBanner(){
  if (orientationBanner) return;
  orientationBanner = document.createElement("div");
  orientationBanner.textContent = "Rotate to portrait for best chat experience.";
  orientationBanner.style.cssText = "position:fixed;bottom:0;left:0;right:0;background:#1F2A44;color:#fff;padding:8px 12px;text-align:center;font-size:12px;z-index:99999;";
  document.body.appendChild(orientationBanner);
}
function hideOrientationBanner(){
  if (!orientationBanner) return;
  orientationBanner.remove();
  orientationBanner = null;
}
function checkOrientation() {
  if (window.innerWidth > window.innerHeight && window.innerWidth < 800) {
    hideOrientationBanner();
    showOrientationBanner();
  } else {
    hideOrientationBanner();
  }
}
window.addEventListener("load", checkOrientation);
window.addEventListener("resize", checkOrientation);

// ---------- Draggable bubble (mouse + touch) + persist position ----------
let dragging = false;
let startX = 0, startY = 0;
let offsetX = 0, offsetY = 0;
const TAP_THRESHOLD = 6;

// Restore last bubble position
(function restoreBubblePos(){
  try {
    const pos = JSON.parse(localStorage.getItem("chat_bubble_pos") || "null");
    if (!pos) return;
    chatBubble.style.left   = (pos.left ?? "") + "px";
    chatBubble.style.top    = (pos.top ?? "") + "px";
    chatBubble.style.right  = "auto";
    chatBubble.style.bottom = "auto";
  } catch {}
})();

function persistBubblePos(){
  if (!chatBubble) return;
  const rect = chatBubble.getBoundingClientRect();
  const left = rect.left + window.scrollX;
  const top  = rect.top  + window.scrollY;
  try { localStorage.setItem("chat_bubble_pos", JSON.stringify({ left, top })); } catch {}
}

// Mouse drag
chatBubble?.addEventListener("mousedown", (e) => {
  dragging = true;
  startX = e.clientX;
  startY = e.clientY;
  const rect = chatBubble.getBoundingClientRect();
  offsetX = e.clientX - rect.left;
  offsetY = e.clientY - rect.top;
  chatBubble.style.transition = "none";
});
document.addEventListener("mousemove", (e) => {
  if (!dragging) return;
  moveBubble(e.clientX, e.clientY);
});
document.addEventListener("mouseup", (e) => {
  if (!dragging) return;
  const moved = Math.abs(e.clientX - startX) > TAP_THRESHOLD || Math.abs(e.clientY - startY) > TAP_THRESHOLD;
  dragging = false;
  chatBubble.style.transition = "";
  persistBubblePos();
  if (!moved) openChat();
});

// Touch drag + tap
chatBubble?.addEventListener("touchstart", (e) => {
  const t = e.touches[0];
  dragging = true;
  startX = t.clientX;
  startY = t.clientY;
  const rect = chatBubble.getBoundingClientRect();
  offsetX = t.clientX - rect.left;
  offsetY = t.clientY - rect.top;
  chatBubble.style.transition = "none";
}, { passive: true });

chatBubble?.addEventListener("touchmove", (e) => {
  if (!dragging) return;
  const t = e.touches[0];
  moveBubble(t.clientX, t.clientY);
  e.preventDefault();
}, { passive: false });

chatBubble?.addEventListener("touchend", (e) => {
  if (!dragging) return;
  dragging = false;
  chatBubble.style.transition = "";
  const t = (e.changedTouches && e.changedTouches[0]) || null;
  const endX = t ? t.clientX : startX;
  const endY = t ? t.clientY : startY;
  const moved = Math.abs(endX - startX) > TAP_THRESHOLD || Math.abs(endY - startY) > TAP_THRESHOLD;
  persistBubblePos();
  if (!moved) openChat();
}, { passive: true });

function moveBubble(clientX, clientY) {
  const winW = window.innerWidth;
  const winH = window.innerHeight;
  const rect = chatBubble.getBoundingClientRect();

  let left = clientX - offsetX;
  let top  = clientY - offsetY;

  if (left < 0) left = 0;
  if (top  < 0) top = 0;
  if (left + rect.width > winW) left = winW - rect.width;
  if (top + rect.height > winH) top = winH - rect.height;

  chatBubble.style.left   = left + "px";
  chatBubble.style.top    = top  + "px";
  chatBubble.style.right  = "auto";
  chatBubble.style.bottom = "auto";
}
