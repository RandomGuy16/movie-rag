// State
let conversationContext = null;
let isGenerating = false;
let defaultModel = "gemini-3.5-flash";
let availableModels = [];

// DOM
const statusDot = document.getElementById('status-dot');
const statusText = document.getElementById('status-text');
const memoryIndicator = document.getElementById('memory-indicator');
const messages = document.getElementById('messages');
const chatForm = document.getElementById('chat-form');
const userPrompt = document.getElementById('user-prompt');
const btnSend = document.getElementById('btn-send');
const btnClearMem = document.getElementById('btn-clear-mem');

const modelSelect = document.getElementById('model-select');
const modelCustom = document.getElementById('model-custom');
const systemPrompt = document.getElementById('system-prompt');
const paramTemp = document.getElementById('param-temp');
const valTemp = document.getElementById('val-temp');
const paramStream = document.getElementById('param-stream');
const payloadPreview = document.getElementById('payload-preview');

// Init
document.addEventListener('DOMContentLoaded', () => {
    checkBackendInfo();
    setupListeners();
    updatePayloadPreview();
});

function setupListeners() {
    paramTemp.addEventListener('input', () => {
        valTemp.textContent = paramTemp.value;
        updatePayloadPreview();
    });

    paramStream.addEventListener('change', updatePayloadPreview);
    systemPrompt.addEventListener('input', updatePayloadPreview);
    modelSelect.addEventListener('change', updatePayloadPreview);
    modelCustom.addEventListener('input', updatePayloadPreview);
    userPrompt.addEventListener('input', updatePayloadPreview);

    userPrompt.addEventListener('input', function () {
        this.style.height = 'auto';
        this.style.height = Math.min(this.scrollHeight, 120) + 'px';
    });

    btnClearMem.addEventListener('click', () => {
        conversationContext = null;
        updateMemoryIndicator();
        addSystemMessage('Conversation memory cleared.');
        updatePayloadPreview();
    });
}

async function checkBackendInfo() {
    try {
        const res = await fetch('/info');
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();

        defaultModel = data.default_model || "gemini-3.5-flash";
        availableModels = data.available_models || [];

        populateModelSelect();

        if (data.genai_status === "connected") {
            statusDot.className = 'dot connected';
            statusText.textContent = `Connected`;
        } else {
            statusDot.className = 'dot warning';
            statusText.textContent = 'API warning';
            addSystemMessage(`GenAI issue: ${data.genai_status}. Check GEMINI_API_KEY.`);
        }
    } catch (err) {
        statusDot.className = 'dot error';
        statusText.textContent = 'Backend offline';
        addSystemMessage(`Could not reach backend: ${err.message}. Is uvicorn running?`);
    }
}

function populateModelSelect() {
    modelSelect.innerHTML = '';
    const models = availableModels.length ? availableModels : [defaultModel];
    models.forEach(name => {
        const opt = document.createElement('option');
        opt.value = name;
        opt.textContent = name;
        if (name === defaultModel) opt.selected = true;
        modelSelect.appendChild(opt);
    });
    if (!models.includes(defaultModel)) {
        const opt = document.createElement('option');
        opt.value = defaultModel;
        opt.textContent = defaultModel;
        opt.selected = true;
        modelSelect.insertBefore(opt, modelSelect.firstChild);
    }
}

function getSelectedModel() {
    const custom = modelCustom.value.trim();
    if (custom) return custom;
    return modelSelect.value || defaultModel;
}

function getPayload(promptText = "") {
    const payload = {
        prompt: promptText || userPrompt.value || "",
        model: getSelectedModel(),
        stream: paramStream.checked,
        temperature: parseFloat(paramTemp.value),
    };
    if (systemPrompt.value.trim()) {
        payload.system = systemPrompt.value.trim();
    }
    if (conversationContext) {
        payload.previous_interaction_id = conversationContext;
    }
    return payload;
}

function updatePayloadPreview() {
    payloadPreview.textContent = JSON.stringify(getPayload(), null, 2);
}

function addSystemMessage(text) {
    const div = document.createElement('div');
    div.className = 'message system';
    div.textContent = text;
    messages.appendChild(div);
    scrollToBottom();
}

function addMessage(sender, text, opts = {}) {
    const div = document.createElement('div');
    div.className = `message ${sender}`;
    if (opts.streaming) div.classList.add('streaming');
    div.textContent = text;
    messages.appendChild(div);
    scrollToBottom();
    return div;
}

function updateMemoryIndicator() {
    if (conversationContext) {
        memoryIndicator.textContent = `Memory: ${conversationContext.slice(0, 12)}...`;
        memoryIndicator.classList.add('active');
    } else {
        memoryIndicator.textContent = 'Memory: empty';
        memoryIndicator.classList.remove('active');
    }
}

function scrollToBottom() {
    messages.scrollTop = messages.scrollHeight;
}

chatForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const prompt = userPrompt.value.trim();
    if (!prompt || isGenerating) return;

    isGenerating = true;
    btnSend.disabled = true;
    userPrompt.value = '';
    userPrompt.style.height = 'auto';

    addMessage('user', prompt);

    const assistantEl = document.createElement('div');
    assistantEl.className = 'message assistant';
    const typing = document.createElement('span');
    typing.className = 'typing';
    typing.innerHTML = '<span></span><span></span><span></span>';
    assistantEl.appendChild(typing);
    messages.appendChild(assistantEl);
    scrollToBottom();

    const payload = getPayload(prompt);
    const start = performance.now();
    updatePayloadPreview();

    try {
        const res = await fetch('/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
        });

        if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            throw new Error(err.detail || `HTTP ${res.status}`);
        }

        assistantEl.innerHTML = '';

        if (payload.stream) {
            const reader = res.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';
            let text = '';
            assistantEl.classList.add('streaming');

            while (true) {
                const { value, done } = await reader.read();
                if (done) break;
                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split('\n');
                buffer = lines.pop();
                for (const line of lines) {
                    if (!line.trim()) continue;
                    try {
                        const data = JSON.parse(line);
                        if (data.error) throw new Error(data.error);
                        if (data.response) {
                            text += data.response;
                            assistantEl.textContent = text;
                            scrollToBottom();
                        }
                        if (data.interaction_id) {
                            conversationContext = data.interaction_id;
                            updateMemoryIndicator();
                        }
                    } catch (err) {
                        console.error('NDJSON parse error', err);
                    }
                }
            }
            assistantEl.classList.remove('streaming');
        } else {
            const data = await res.json();
            assistantEl.textContent = data.response || '';
            if (data.interaction_id) {
                conversationContext = data.interaction_id;
                updateMemoryIndicator();
            }
        }
    } catch (err) {
        assistantEl.classList.remove('streaming');
        assistantEl.textContent = `Error: ${err.message}`;
        console.error(err);
    } finally {
        isGenerating = false;
        btnSend.disabled = false;
        scrollToBottom();
        updatePayloadPreview();
    }
});
