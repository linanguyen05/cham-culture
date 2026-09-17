const input = document.getElementById("userInput");
input.addEventListener("keydown", function(event) {
    if (event.key === "Enter") {
        event.preventDefault();
        sendMessage();
    }
});

function sendMessage() {
    let msg = input.value.trim();
    if (!msg) return;
    let chatbox = document.getElementById("chatbox");

    // Tin nhắn người dùng
    let userMsg = document.createElement("div");
    userMsg.className = "message user";
    userMsg.innerHTML = `<div class="avatar">👤</div><div class="bubble">${msg}</div>`;
    chatbox.appendChild(userMsg);

    // Hiển thị icon loading cho BOT
    let loadingIcon = document.createElement("div");
    loadingIcon.className = "message bot";
    loadingIcon.innerHTML = `<div class="avatar">🤖</div><div class="bubble"><div class="loading"></div></div>`;
    chatbox.appendChild(loadingIcon);
    chatbox.scrollTop = chatbox.scrollHeight;

    // Gửi request tới server
    fetch("/api/chatbot/chat", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({message: msg})
    })
    .then(res => res.json())
    .then(data => {
        chatbox.removeChild(loadingIcon);
        
        let botMsg = document.createElement("div");
        botMsg.className = "message bot";
        
        // Escape HTML to prevent XSS but allow basic newlines formatting if any
        const safeReply = data.reply ? data.reply.replace(/</g, "&lt;").replace(/>/g, "&gt;") : "Có lỗi xảy ra, không nhận được phản hồi.";
        
        botMsg.innerHTML = `<div class="avatar">🤖</div><div class="bubble">${safeReply}</div>`;
        chatbox.appendChild(botMsg);
        chatbox.scrollTop = chatbox.scrollHeight;
        
        if (data.count !== undefined && data.limit !== undefined) {
            document.getElementById("counter").innerText = `${data.count}/${data.limit}`;
        }
    })
    .catch(err => {
        console.error("Chat error:", err);
        chatbox.removeChild(loadingIcon);
        let errorMsg = document.createElement("div");
        errorMsg.className = "message bot";
        errorMsg.innerHTML = `<div class="avatar">🤖</div><div class="bubble" style="color: red;">Lỗi kết nối. Vui lòng thử lại sau.</div>`;
        chatbox.appendChild(errorMsg);
        chatbox.scrollTop = chatbox.scrollHeight;
    });

    input.value = "";
}
