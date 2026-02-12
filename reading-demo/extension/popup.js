const chat = document.getElementById("chat");
const msg = document.getElementById("msg");
const send = document.getElementById("send");

function addLine(role, text, citations) {
  const div = document.createElement("div");
  div.className = "msg";

  const who = document.createElement("div");
  who.className = role === "user" ? "user" : "assistant";
  who.textContent = role === "user" ? "You" : "Assistant";
  div.appendChild(who);

  const body = document.createElement("div");
  body.textContent = text;
  div.appendChild(body);

  if (citations && citations.length) {
    const cites = document.createElement("div");
    cites.className = "cites";
    cites.textContent = "Citations: " + citations.map(c => `[${c.tag}] ${c.title ?? ""} p.${c.page ?? "?"}`).join(" | ");
    div.appendChild(cites);
  }

  chat.appendChild(div);
  chat.scrollTop = chat.scrollHeight;
}

async function sendMessage() {
  const text = msg.value.trim();
  if (!text) return;

  addLine("user", text);
  msg.value = "";

  try {
    const res = await fetch("http://127.0.0.1:8000/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message: text,
        courseId: "demo-course",
        tenantId: "demo-tenant"
      })
    });

    const data = await res.json();
    addLine("assistant", data.answer ?? "(no answer)", data.citations ?? []);
  } catch (e) {
    addLine("assistant", "Error calling backend: " + e.message);
  }
}

send.addEventListener("click", sendMessage);
msg.addEventListener("keydown", (e) => {
  if (e.key === "Enter") sendMessage();
});
