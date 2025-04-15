// 初始化音频播放器
const audioPlayer = new AudioPlayer('/static');

// 处理文本到语音的转换和播放
async function speakText(text) {
    try {
        const response = await fetch('/api/llm/tts', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ text })
        });

        if (!response.ok) {
            throw new Error('TTS request failed');
        }

        const audioBlob = await response.blob();
        const audioUrl = URL.createObjectURL(audioBlob);
        const audio = new Audio(audioUrl);
        audio.play();
    } catch (error) {
        console.error('Error playing TTS:', error);
    }
}

// 处理聊天消息发送
async function sendMessage() {
    const messageInput = document.getElementById('message-input');
    const chatMessages = document.getElementById('chat-messages');
    const message = messageInput.value.trim();
    
    if (!message) return;
    
    // 清空输入框
    messageInput.value = '';
    
    // 添加用户消息到聊天界面
    const userMessageDiv = document.createElement('div');
    userMessageDiv.className = 'message user-message';
    userMessageDiv.textContent = message;
    chatMessages.appendChild(userMessageDiv);
    
    try {
        // 发送消息到Ollama
        const response = await fetch('/api/llm/generate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                model: "qwen:7b",
                prompt: message,
                stream: true
            })
        });

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let botMessage = '';
        const botMessageDiv = document.createElement('div');
        botMessageDiv.className = 'message bot-message';
        chatMessages.appendChild(botMessageDiv);

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            const chunk = decoder.decode(value);
            const lines = chunk.split('\n');
            
            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    try {
                        const data = JSON.parse(line.slice(6));
                        if (data.response) {
                            botMessage += data.response;
                            botMessageDiv.textContent = botMessage;
                        }
                    } catch (e) {
                        console.error('Error parsing JSON:', e);
                    }
                }
            }
        }

        // 朗读回复
        await speakText(botMessage);
        
    } catch (error) {
        console.error('Error:', error);
        const errorDiv = document.createElement('div');
        errorDiv.className = 'message error-message';
        errorDiv.textContent = '发生错误，请重试';
        chatMessages.appendChild(errorDiv);
    }
    
    // 滚动到底部
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// 监听发送按钮点击事件
document.getElementById('send-button').addEventListener('click', sendMessage);

// 监听输入框回车事件
document.getElementById('message-input').addEventListener('keypress', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
}); 