document.addEventListener('DOMContentLoaded', () => {
    // --- DOM Elements ---
    const chatView = document.getElementById('chat-view');
    const agentView = document.getElementById('agent-view');
    const btnToggleChat = document.getElementById('toggle-chat-btn');
    const btnToggleAgent = document.getElementById('toggle-agent-btn');
    
    const pdfUpload = document.getElementById('pdf-upload');
    const uploadBtn = document.getElementById('upload-btn');
    const uploadStatus = document.getElementById('upload-status');
    
    const chatInput = document.getElementById('chat-input');
    const sendBtn = document.getElementById('send-btn');
    const chatBox = document.getElementById('chat-box');
    
    const refreshEscalationsBtn = document.getElementById('refresh-escalations-btn');
    const escalationContainer = document.getElementById('escalation-container');
    const escalationTemplate = document.getElementById('escalation-template');

    // --- State ---
    let currentSessionId = "session_" + Math.floor(Math.random() * 10000);

    // --- View Toggling ---
    function switchView(view) {
        if (view === 'chat') {
            chatView.style.display = 'flex';
            agentView.style.display = 'none';
            btnToggleChat.classList.add('active');
            btnToggleAgent.classList.remove('active');
        } else {
            chatView.style.display = 'none';
            agentView.style.display = 'flex';
            btnToggleChat.classList.remove('active');
            btnToggleAgent.classList.add('active');
            fetchEscalations();
        }
    }

    btnToggleChat.addEventListener('click', () => switchView('chat'));
    btnToggleAgent.addEventListener('click', () => switchView('agent'));

    // --- PDF Upload ---
    pdfUpload.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            uploadBtn.disabled = false;
        } else {
            uploadBtn.disabled = true;
        }
    });

    uploadBtn.addEventListener('click', async () => {
        const file = pdfUpload.files[0];
        if (!file) return;

        const formData = new FormData();
        formData.append('file', file);

        uploadBtn.disabled = true;
        uploadBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Processing...';
        uploadStatus.innerText = '';

        try {
            const res = await fetch('/api/upload', {
                method: 'POST',
                body: formData
            });
            const data = await res.json();
            if (res.ok) {
                uploadStatus.style.color = 'var(--success)';
                uploadStatus.innerText = 'Knowledge Base Updated!';
                addMessage('System', 'Knowledge base has been updated successfully. You can now ask questions about the document.', 'system');
            } else {
                uploadStatus.style.color = 'var(--danger)';
                uploadStatus.innerText = data.detail || 'Upload failed.';
            }
        } catch (err) {
            uploadStatus.style.color = 'var(--danger)';
            uploadStatus.innerText = 'Connection error.';
        } finally {
            uploadBtn.innerHTML = '<i class="fa-solid fa-cloud-arrow-up"></i> Upload & Process';
            pdfUpload.value = '';
            // keep disabled until new file is selected
        }
    });

    // --- Chat Interface ---
    function addMessage(sender, text, type = 'user') {
        const msgDiv = document.createElement('div');
        msgDiv.className = `message ${type}`;
        
        const iconClass = type === 'user' ? 'fa-user' : 'fa-robot';
        
        msgDiv.innerHTML = `
            <div class="avatar"><i class="fa-solid ${iconClass}"></i></div>
            <div class="bubble">${text}</div>
        `;
        
        chatBox.appendChild(msgDiv);
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    function addTypingIndicator() {
        const msgDiv = document.createElement('div');
        msgDiv.className = 'message system typing';
        msgDiv.id = 'typing-indicator';
        msgDiv.innerHTML = `
            <div class="avatar"><i class="fa-solid fa-robot"></i></div>
            <div class="bubble typing-indicator">
                <div class="dot"></div><div class="dot"></div><div class="dot"></div>
            </div>
        `;
        chatBox.appendChild(msgDiv);
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    function removeTypingIndicator() {
        const indicator = document.getElementById('typing-indicator');
        if (indicator) indicator.remove();
    }

    async function sendMessage() {
        const text = chatInput.value.trim();
        if (!text) return;

        // User message UI
        addMessage('You', text, 'user');
        chatInput.value = '';
        addTypingIndicator();

        try {
            const res = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query: text, thread_id: currentSessionId })
            });
            const data = await res.json();
            removeTypingIndicator();

            if (res.ok) {
                if (data.status === 'escalated') {
                    addMessage('System', data.message, 'system');
                    // Alert Agent Dashboard visually
                    btnToggleAgent.style.color = 'var(--warning)';
                    setTimeout(() => { btnToggleAgent.style.color = ''; }, 3000);
                } else {
                    addMessage('AI', data.answer, 'system');
                }
            } else {
                addMessage('System', 'Error processing request.', 'system');
            }
        } catch (err) {
            removeTypingIndicator();
            addMessage('System', 'Network error.', 'system');
        }
    }

    sendBtn.addEventListener('click', sendMessage);
    chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendMessage();
    });

    // --- Agent Dashboard ---
    async function fetchEscalations() {
        try {
            refreshEscalationsBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i>';
            const res = await fetch('/api/escalations');
            const data = await res.json();
            refreshEscalationsBtn.innerHTML = '<i class="fa-solid fa-arrows-rotate"></i> Refresh';

            renderEscalations(data);
        } catch (err) {
            console.error(err);
            refreshEscalationsBtn.innerHTML = '<i class="fa-solid fa-arrows-rotate"></i> Refresh';
        }
    }

    refreshEscalationsBtn.addEventListener('click', fetchEscalations);

    function renderEscalations(escalations) {
        // Clear current (keep empty state hidden or visible)
        escalationContainer.innerHTML = '';

        if (!escalations || escalations.length === 0) {
            escalationContainer.innerHTML = `
                <div class="empty-state">
                    <i class="fa-solid fa-check-circle"></i>
                    <p>No active escalations. The AI is handling everything!</p>
                </div>
            `;
            return;
        }

        escalations.forEach(esc => {
            const clone = escalationTemplate.content.cloneNode(true);
            const card = clone.querySelector('.escalation-card');
            
            clone.querySelector('.thread-id').innerText = esc.thread_id;
            clone.querySelector('.reason-badge').innerText = esc.reason;
            clone.querySelector('.user-query').innerText = esc.query;
            clone.querySelector('.ai-draft').innerText = esc.draft_answer || 'No draft generated.';
            
            const contextDiv = clone.querySelector('.context-snippets');
            if (esc.context && esc.context.length > 0) {
                contextDiv.innerText = esc.context.join('\n\n---\n\n');
            } else {
                contextDiv.innerText = "No relevant context found in Knowledge Base.";
            }

            const resolveBtn = clone.querySelector('.resolve-btn');
            const replyInput = clone.querySelector('.agent-reply-input');

            resolveBtn.addEventListener('click', async () => {
                const resolutionText = replyInput.value.trim();
                if (!resolutionText) {
                    alert("Please provide a resolution before sending.");
                    return;
                }

                resolveBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Sending...';
                resolveBtn.disabled = true;

                try {
                    const res = await fetch('/api/resolve', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            thread_id: esc.thread_id,
                            human_input: resolutionText
                        })
                    });

                    if (res.ok) {
                        card.remove();
                        // If this was the current session in chat, update the chat box too
                        if (esc.thread_id === currentSessionId) {
                            addMessage('Agent', resolutionText, 'system');
                        }
                        fetchEscalations(); // check if empty
                    } else {
                        alert("Failed to resolve.");
                        resolveBtn.innerHTML = 'Resolve & Send';
                        resolveBtn.disabled = false;
                    }
                } catch (err) {
                    alert("Network error.");
                    resolveBtn.innerHTML = 'Resolve & Send';
                    resolveBtn.disabled = false;
                }
            });

            escalationContainer.appendChild(clone);
        });
    }
});
