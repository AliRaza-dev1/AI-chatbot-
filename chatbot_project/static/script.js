const chatArea = document.getElementById('chatArea');
const messageInput = document.getElementById('messageInput');
const sendBtn = document.getElementById('sendBtn');
const voiceBtn = document.getElementById('voiceBtn');
const speakBtn = document.getElementById('speakBtn');
const suggestionChips = document.querySelectorAll('.suggestion-chip');

let lastBotResponse = '';

function addMessage(text, isUser = false) {
    const messageBox = document.createElement('div');
    messageBox.className = `message-box ${isUser ? 'user-message' : 'bot-message'}`;
    
    const messageContent = document.createElement('div');
    messageContent.className = 'message-content';
    messageContent.textContent = text;
    
    messageBox.appendChild(messageContent);
    chatArea.appendChild(messageBox);
    chatArea.scrollTop = chatArea.scrollHeight;
}

function showStatus(text) {
    const status = document.createElement('div');
    status.className = 'status-bubble';
    status.textContent = text;
    chatArea.appendChild(status);
    chatArea.scrollTop = chatArea.scrollHeight;
    
    setTimeout(() => status.remove(), 3000);
}

async function sendMessage(text) {
    if (!text.trim()) return;
    
    addMessage(text, true);
    messageInput.value = '';
    
    try {
        const response = await fetch('/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ message: text })
        });
        
        const data = await response.json();
        lastBotResponse = data.response;
        addMessage(data.response, false);
        
    } catch (error) {
        addMessage('Error: Could not connect to server.', false);
    }
}

async function handleVoice() {
    voiceBtn.disabled = true;
    voiceBtn.textContent = '⏳';
    showStatus('🎤 Listening... Please speak now');
    
    try {
        const response = await fetch('/voice', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const data = await response.json();
        
        if (data.success) {
            addMessage(data.text, true);
            addMessage(data.response, false);
            lastBotResponse = data.response;
        } else {
            showStatus(`❌ ${data.error}`);
        }
        
    } catch (error) {
        showStatus('❌ Error: Could not connect to server');
    } finally {
        voiceBtn.disabled = false;
        voiceBtn.textContent = '🎤';
    }
}

async function handleSpeak() {
    if (!lastBotResponse) {
        showStatus('No response to speak');
        return;
    }
    
    speakBtn.disabled = true;
    speakBtn.textContent = '⏳';
    showStatus('🔊 Speaking...');
    
    try {
        await fetch('/speak', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ text: lastBotResponse })
        });
        
        const wordCount = lastBotResponse.split(' ').length;
        const estimatedTime = (wordCount / 2.5) * 1000;
        
        setTimeout(() => {
            speakBtn.disabled = false;
            speakBtn.textContent = '🔊';
        }, estimatedTime);
        
    } catch (error) {
        showStatus('❌ Error: Could not speak response');
        speakBtn.disabled = false;
        speakBtn.textContent = '🔊';
    }
}

sendBtn.addEventListener('click', () => sendMessage(messageInput.value));

messageInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') sendMessage(messageInput.value);
});

voiceBtn.addEventListener('click', handleVoice);
speakBtn.addEventListener('click', handleSpeak);

suggestionChips.forEach(chip => {
    chip.addEventListener('click', () => {
        const question = chip.getAttribute('data-q');
        sendMessage(question);
    });
});

messageInput.focus();