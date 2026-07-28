// App State
let conversationContext = null; // Stores previous_interaction_id
let isGenerating = false;
let configuredModelName = "gemini-3.5-flash";

// DOM Elements
const connectionDot = document.getElementById('connection-dot');
const connectionText = document.getElementById('connection-text');
const modelBadge = document.getElementById('model-badge');
const chatMemoryIndicator = document.getElementById('chat-memory-indicator');
const messagesContainer = document.getElementById('messages-container');
const chatForm = document.getElementById('chat-form');
const userPromptInput = document.getElementById('user-prompt');
const btnSend = document.getElementById('btn-send');
const btnClearMem = document.getElementById('btn-clear-mem');

// Sliders and Inputs
const paramSystem = document.getElementById('system-prompt');
const paramTemp = document.getElementById('param-temp');
const paramTopP = document.getElementById('param-top-p');
const paramTopK = document.getElementById('param-top-k');
const paramMaxTokens = document.getElementById('param-max-tokens');
const paramRepPenalty = document.getElementById('param-rep-penalty');
const paramStream = document.getElementById('param-stream');

// Sliders value displays
const valTemp = document.getElementById('val-temp');
const valTopP = document.getElementById('val-top-p');
const valTopK = document.getElementById('val-top-k');
const valMaxTokens = document.getElementById('val-max-tokens');
const valRepPenalty = document.getElementById('val-rep-penalty');

// Code previews
const payloadPreview = document.getElementById('payload-preview');
const curlPreview = document.getElementById('curl-preview');

// Stats Displays
const statSpeed = document.getElementById('stat-speed');
const statTime = document.getElementById('stat-time');
const statTokens = document.getElementById('stat-tokens');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    setupSliderListeners();
    setupTabListeners();
    setupCopyButtons();
    checkBackendInfo();
    updateApiInspector();
    
    // Auto-resize user prompt textarea
    userPromptInput.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = (this.scrollHeight) + 'px';
    });
});

// Setup range sliders listeners
function setupSliderListeners() {
    const sliders = [
        { input: paramTemp, display: valTemp },
        { input: paramTopP, display: valTopP },
        { input: paramTopK, display: valTopK },
        { input: paramMaxTokens, display: valMaxTokens },
        { input: paramRepPenalty, display: valRepPenalty }
    ];
    
    sliders.forEach(item => {
        item.input.addEventListener('input', (e) => {
            item.display.textContent = e.target.value;
            updateApiInspector();
        });
    });
    
    if (paramSystem) paramSystem.addEventListener('input', updateApiInspector);
    userPromptInput.addEventListener('input', updateApiInspector);
    paramStream.addEventListener('change', updateApiInspector);
}

// Setup API Inspector Tabs
function setupTabListeners() {
    const tabButtons = document.querySelectorAll('.tab-btn');
    tabButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            tabButtons.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            
            const targetTabId = btn.getAttribute('data-tab');
            document.querySelectorAll('.tab-content').forEach(content => {
                content.classList.add('hidden');
            });
            document.getElementById(targetTabId).classList.remove('hidden');
        });
    });
}

// Copy Code Snippets to Clipboard
function setupCopyButtons() {
    const copyBtns = document.querySelectorAll('.copy-btn');
    copyBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const targetId = btn.getAttribute('data-copy-target');
            const codeEl = document.getElementById(targetId);
            
            navigator.clipboard.writeText(codeEl.textContent).then(() => {
                btn.textContent = 'Copied!';
                btn.classList.add('copied');
                setTimeout(() => {
                    btn.textContent = 'Copy';
                    btn.classList.remove('copied');
                }, 2000);
            }).catch(err => {
                console.error('Failed to copy text: ', err);
            });
        });
    });
}

// Query FastAPI server stats and model mapping
async function checkBackendInfo() {
    try {
        const response = await fetch('/info');
        if (!response.ok) throw new Error(`Server returned ${response.status}`);
        const data = await response.json();
        
        configuredModelName = data.default_model || "gemini-3.5-flash";
        modelBadge.textContent = configuredModelName;
        
        if (data.genai_status === "connected") {
            connectionDot.className = 'dot connected';
            connectionText.textContent = `Connected (GenAI API: ${configuredModelName})`;
        } else {
            connectionDot.className = 'dot warning';
            connectionText.textContent = 'GenAI API Warning';
            appendSystemMessage(`GenAI API issue: ${data.genai_status}. Check your GEMINI_API_KEY environment variable.`);
        }
    } catch (error) {
        connectionDot.className = 'dot error';
        connectionText.textContent = 'Backend Offline';
        appendSystemMessage(`Could not connect to FastAPI backend: ${error.message}. Is uvicorn running?`);
    }
}

// Compile payload based on current settings
function getRequestPayload(promptText = "") {
    const payload = {
        prompt: promptText || userPromptInput.value || "Recommend a good sci-fi movie.",
        model: configuredModelName || "gemini-3.5-flash",
        stream: paramStream.checked
    };
    
    if (conversationContext) {
        payload.previous_interaction_id = conversationContext;
    }
    
    return payload;
}


// Refreshes API payload preview block
function updateApiInspector() {
    const payload = getRequestPayload();
    payloadPreview.textContent = JSON.stringify(payload, null, 2);
    
    // Format Curl command
    const hostUrl = window.location.origin;
    const curlCommand = `curl -X POST "${hostUrl}/chat" \\
  -H "Content-Type: application/json" \\
  -d '${JSON.stringify(payload, null, 2).replace(/'/g, "'\\''")}'`;
  
    curlPreview.textContent = curlCommand;
}

// Append System Message log
function appendSystemMessage(text) {
    const div = document.createElement('div');
    div.className = 'system-message';
    div.textContent = text;
    messagesContainer.appendChild(div);
    scrollToBottom();
}

// Scrolls chat box
function scrollToBottom() {
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

// Clear memory
btnClearMem.addEventListener('click', () => {
    conversationContext = null;
    chatMemoryIndicator.textContent = 'Session Memory: Empty';
    chatMemoryIndicator.classList.remove('active');
    appendSystemMessage("Conversation history memory cleared.");
    updateApiInspector();
});

// Chat form submission logic
chatForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const prompt = userPromptInput.value.trim();
    if (!prompt || isGenerating) return;
    
    isGenerating = true;
    btnSend.disabled = true;
    userPromptInput.value = '';
    userPromptInput.style.height = 'auto'; // Reset text area height
    
    // 1. Append User Bubble
    appendMessage('user', prompt);
    
    // 2. Append Assistant Bubble placeholder with loading indicator
    const assistantMsgEl = appendMessage('assistant', '');
    const bubbleEl = assistantMsgEl.querySelector('.msg-bubble');
    
    const loader = document.createElement('div');
    loader.className = 'typing-indicator';
    loader.innerHTML = '<span></span><span></span><span></span>';
    bubbleEl.appendChild(loader);
    
    scrollToBottom();
    
    // Get payload
    const payload = getRequestPayload(prompt);
    const startTime = performance.now();
    
    try {
        const response = await fetch('/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });
        
        if (!response.ok) {
            const errData = await response.json();
            throw new Error(errData.detail || `Server error: ${response.status}`);
        }
        
        // Remove typing loader
        bubbleEl.innerHTML = '';
        
        if (payload.stream) {
            // Streaming handler (NDJSON)
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';
            let completeText = '';
            bubbleEl.classList.add('streaming-text');
            
            while (true) {
                const { value, done } = await reader.read();
                if (done) break;
                
                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split('\n');
                buffer = lines.pop(); // save incomplete trailing line
                
                for (const line of lines) {
                    if (line.trim() === '') continue;
                    
                    try {
                        const data = JSON.parse(line);
                        
                        if (data.error) {
                            throw new Error(data.error);
                        }
                        
                        if (data.response) {
                            completeText += data.response;
                            bubbleEl.textContent = completeText;
                            scrollToBottom();
                        }
                        
                        if (data.interaction_id) {
                            conversationContext = data.interaction_id;
                            updateMemoryIndicator();
                        }
                    } catch (e) {
                        console.error('Line parsing error', e);
                    }
                }
            }
            bubbleEl.classList.remove('streaming-text');
            const totalSecs = ((performance.now() - startTime) / 1000).toFixed(2);
            statTime.textContent = `Time: ${totalSecs}s`;
            statSpeed.textContent = `Mode: Streamed`;
            statTokens.textContent = `Memory ID: ${conversationContext ? conversationContext.slice(0, 12) + '...' : 'None'}`;

        } else {
            // Single generation handler
            const data = await response.json();
            bubbleEl.textContent = data.response;
            if (data.interaction_id) {
                conversationContext = data.interaction_id;
                updateMemoryIndicator();
            }
            const totalSecs = ((performance.now() - startTime) / 1000).toFixed(2);
            statTime.textContent = `Time: ${totalSecs}s`;
            statSpeed.textContent = `Mode: Standard`;
            statTokens.textContent = `Memory ID: ${conversationContext ? conversationContext.slice(0, 12) + '...' : 'None'}`;
        }
        
    } catch (err) {
        bubbleEl.innerHTML = '';
        bubbleEl.textContent = `⚠️ Error generating response: ${err.message}`;
        console.error(err);
    } finally {
        isGenerating = false;
        btnSend.disabled = false;
        scrollToBottom();
        updateApiInspector(); // Update context representation in JSON preview
    }
});

// Appends message to DOM
function appendMessage(sender, text) {
    const msgDiv = document.createElement('div');
    msgDiv.className = `msg ${sender}`;
    
    const senderSpan = document.createElement('span');
    senderSpan.className = 'msg-sender';
    senderSpan.textContent = sender === 'user' ? 'You' : configuredModelName;
    
    const bubbleDiv = document.createElement('div');
    bubbleDiv.className = 'msg-bubble';
    bubbleDiv.textContent = text;
    
    msgDiv.appendChild(senderSpan);
    msgDiv.appendChild(bubbleDiv);
    messagesContainer.appendChild(msgDiv);
    return msgDiv;
}

// Updates session token context indicators
function updateMemoryIndicator() {
    if (conversationContext) {
        chatMemoryIndicator.textContent = `Session Memory: Active (${conversationContext.slice(0, 16)}...)`;
        chatMemoryIndicator.classList.add('active');
    } else {
        chatMemoryIndicator.textContent = 'Session Memory: Empty';
        chatMemoryIndicator.classList.remove('active');
    }
}

