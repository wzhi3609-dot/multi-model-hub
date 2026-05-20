let currentConversationId = null;
let currentModel = "auto";
let isAutoRoute = true;
let isStreaming = false;
let modelsData = [];
let tagsData = {};

document.addEventListener("DOMContentLoaded", () => {
    init();
});

async function init() {
    marked.setOptions({ breaks: true, gfm: true });
    await loadModels();
    await loadConversations();
    bindEvents();
    autoResizeTextarea();
}

async function loadModels() {
    try {
        const res = await fetch("/api/models");
        const data = await res.json();
        modelsData = data.models;
        tagsData = data.tags;
        renderModelPanel();
        renderModelSelect();
        renderTagList();
    } catch (e) {
        console.error("加载模型列表失败", e);
    }
}

function renderModelPanel() {
    const container = document.getElementById("modelList");
    const colors = ["", "green", "orange", "blue", "purple"];
    container.innerHTML = modelsData.map((m, i) => `
        <div class="model-card ${m.enabled ? "enabled" : "disabled"}">
            <div class="model-name">${m.display_name}</div>
            <div class="model-desc">${m.description}</div>
            <div class="model-tags">
                ${m.tags.map((t, j) => `<span class="tag-badge ${colors[j % colors.length]}">${t}</span>`).join("")}
            </div>
        </div>
    `).join("");
}

function renderModelSelect() {
    const select = document.getElementById("modelSelect");
    const enabledModels = modelsData.filter(m => m.enabled);
    select.innerHTML = `
        <option value="auto">自动选择</option>
        ${enabledModels.map(m => `<option value="${m.key}">${m.display_name}</option>`).join("")}
    `;
}

function renderTagList() {
    const container = document.getElementById("tagList");
    if (!Object.keys(tagsData).length) return;
    container.innerHTML = Object.values(tagsData)
        .filter(t => t.keywords && t.keywords.length > 0)
        .map(t => `
            <div class="tag-item">
                <span class="tag-name">${t.name}</span>
                <span class="tag-examples">${t.keywords.slice(0, 5).join(", ")}</span>
            </div>
        `).join("");
}

async function loadConversations() {
    try {
        const res = await fetch("/api/conversations");
        const data = await res.json();
        renderConversationList(data.conversations || []);
    } catch (e) {
        console.error("加载对话列表失败", e);
    }
}

function renderConversationList(conversations) {
    const container = document.getElementById("conversationList");
    if (!conversations.length) {
        container.innerHTML = `<div style="color:var(--text-secondary);font-size:12px;padding:12px;text-align:center;">暂无对话</div>`;
        return;
    }
    container.innerHTML = conversations.map(c => `
        <div class="conversation-item ${c.id === currentConversationId ? "active" : ""}"
             data-id="${c.id}" onclick="switchConversation('${c.id}')">
            <span style="overflow:hidden;text-overflow:ellipsis;">${c.title || "新对话"}</span>
            <span class="delete-icon" onclick="event.stopPropagation();deleteConversation('${c.id}')" title="删除">×</span>
        </div>
    `).join("");
}

function bindEvents() {
    document.getElementById("sendBtn").addEventListener("click", sendMessage);
    document.getElementById("newChatBtn").addEventListener("click", newConversation);

    const input = document.getElementById("userInput");
    input.addEventListener("keydown", (e) => {
        if (e.ctrlKey && e.key === "Enter") {
            e.preventDefault();
            sendMessage();
        }
    });
    input.addEventListener("input", autoResizeTextarea);

    const autoToggle = document.getElementById("autoRouteToggle");
    autoToggle.addEventListener("change", () => {
        isAutoRoute = autoToggle.checked;
        document.getElementById("modelSelect").disabled = isAutoRoute;
    });

    const modelSelect = document.getElementById("modelSelect");
    modelSelect.addEventListener("change", () => {
        currentModel = modelSelect.value;
    });
}

function autoResizeTextarea() {
    const textarea = document.getElementById("userInput");
    textarea.style.height = "auto";
    textarea.style.height = Math.min(textarea.scrollHeight, 200) + "px";
}

function newConversation() {
    if (isStreaming) return;
    currentConversationId = null;
    currentModel = "auto";
    document.getElementById("userInput").value = "";
    document.getElementById("messageArea").innerHTML = `
        <div class="welcome-screen">
            <h1>Multi-Model Hub</h1>
            <p>集成多模型，智能调度。开始对话吧！</p>
        </div>
    `;
    loadConversations();
}

async function switchConversation(id) {
    if (isStreaming) return;
    try {
        const res = await fetch(`/api/conversations/${id}`);
        const conv = await res.json();
        if (conv.error) { showToast(conv.error, "error"); return; }

        currentConversationId = conv.id;
        currentModel = conv.model || "auto";

        const autoToggle = document.getElementById("autoRouteToggle");
        const modelSelect = document.getElementById("modelSelect");
        if (currentModel === "auto") {
            autoToggle.checked = true;
            isAutoRoute = true;
            modelSelect.disabled = true;
            modelSelect.value = "auto";
        } else {
            autoToggle.checked = false;
            isAutoRoute = false;
            modelSelect.disabled = false;
            modelSelect.value = currentModel;
        }

        renderMessages(conv.messages || []);
        loadConversations();
    } catch (e) {
        console.error("切换对话失败", e);
    }
}

function renderMessages(messages) {
    const area = document.getElementById("messageArea");
    if (!messages.length) {
        area.innerHTML = `<div class="welcome-screen"><h1>Multi-Model Hub</h1><p>开始对话吧！</p></div>`;
        return;
    }
    area.innerHTML = messages.map(m => createMessageHTML(m)).join("");
    area.scrollTop = area.scrollHeight;
    if (window.hljs) {
        area.querySelectorAll("pre code").forEach(b => hljs.highlightElement(b));
    }
}

function createMessageHTML(msg) {
    const roleClass = msg.role === "user" ? "user" : "assistant";
    const meta = msg.model ? `<div class="message-meta">${msg.model}</div>` : "";
    const content = msg.role === "assistant" ? marked.parse(msg.content) : escapeHtml(msg.content);
    return `
        <div class="message-row ${roleClass}">
            ${meta}
            <div class="message-bubble">${content}</div>
        </div>
    `;
}

function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
}

async function sendMessage() {
    if (isStreaming) return;

    const input = document.getElementById("userInput");
    const message = input.value.trim();
    if (!message) return;

    const effectiveModel = isAutoRoute ? null : currentModel;
    const convId = currentConversationId;

    appendUserMessage(message);
    input.value = "";
    autoResizeTextarea();

    const assistantRow = appendAssistantRow();
    const bubble = assistantRow.querySelector(".message-bubble");

    isStreaming = true;
    document.getElementById("sendBtn").disabled = true;

    try {
        const response = await fetch("/api/chat/send", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                message: message,
                conversation_id: convId,
                model: effectiveModel,
            }),
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";
        let fullContent = "";
        let routingInfo = null;
        let resolvedConversationId = convId;

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split("\n");
            buffer = lines.pop() || "";

            for (const line of lines) {
                if (line.startsWith("data: ")) {
                    try {
                        const event = JSON.parse(line.slice(6));

                        if (event.type === "token") {
                            fullContent += event.content;
                            bubble.innerHTML = marked.parse(fullContent);
                            if (window.hljs) {
                                bubble.querySelectorAll("pre code").forEach(b => hljs.highlightElement(b));
                            }
                            scrollToBottom();
                        } else if (event.type === "routing") {
                            routingInfo = event;
                            const meta = assistantRow.querySelector(".message-meta");
                            meta.textContent = `${event.model_name || event.model} · ${event.reason}`;
                        } else if (event.type === "conversation_id") {
                            resolvedConversationId = event.id;
                            if (!currentConversationId) {
                                currentConversationId = event.id;
                            }
                        } else if (event.type === "error") {
                            bubble.innerHTML = `<span style="color:var(--danger);">错误: ${escapeHtml(event.message)}</span>`;
                            showToast(event.message, "error");
                        }
                    } catch (e) {
                        // 忽略解析错误
                    }
                }
            }
        }

        if (!currentConversationId && resolvedConversationId) {
            currentConversationId = resolvedConversationId;
        }

        if (currentConversationId) {
            await updateModelIfNeeded(resolvedConversationId || currentConversationId, routingInfo);
        }

    } catch (e) {
        bubble.innerHTML = `<span style="color:var(--danger);">请求失败: ${escapeHtml(e.message)}</span>`;
        showToast(e.message, "error");
    } finally {
        isStreaming = false;
        document.getElementById("sendBtn").disabled = false;
        loadConversations();
    }
}

async function updateModelIfNeeded(convId, routingInfo) {
    if (!routingInfo) return;
    try {
        await fetch(`/api/conversations/${convId}?model=${routingInfo.model}`, { method: "PUT" });
    } catch (e) {}
}

function appendUserMessage(message) {
    const area = document.getElementById("messageArea");
    const welcome = area.querySelector(".welcome-screen");
    if (welcome) welcome.remove();

    const row = document.createElement("div");
    row.className = "message-row user";
    row.innerHTML = `<div class="message-bubble">${escapeHtml(message)}</div>`;
    area.appendChild(row);
    scrollToBottom();
}

function appendAssistantRow() {
    const area = document.getElementById("messageArea");
    const row = document.createElement("div");
    row.className = "message-row assistant";
    row.innerHTML = `
        <div class="message-meta">思考中...</div>
        <div class="message-bubble"><span class="typing-indicator"></span></div>
    `;
    area.appendChild(row);
    scrollToBottom();
    return row;
}

async function deleteConversation(id) {
    if (isStreaming) return;
    if (!confirm("确定删除该对话？")) return;

    try {
        await fetch(`/api/conversations/${id}`, { method: "DELETE" });
        if (currentConversationId === id) {
            newConversation();
        }
        loadConversations();
    } catch (e) {
        showToast("删除失败", "error");
    }
}

function scrollToBottom() {
    const area = document.getElementById("messageArea");
    area.scrollTop = area.scrollHeight;
}

function showToast(msg, type) {
    const toast = document.getElementById("toast");
    toast.textContent = msg;
    toast.className = "toast show" + (type === "error" ? " error" : "");
    clearTimeout(toast._timeout);
    toast._timeout = setTimeout(() => {
        toast.className = "toast";
    }, 3000);
}
