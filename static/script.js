/**
 * DAMN - 前端交互逻辑
 * ChatGPT 风格的对话界面
 */

// API 基础地址
const API_BASE = '';

// DOM 元素
const messagesContainer = document.getElementById('messagesContainer');
const messageInput = document.getElementById('messageInput');
const sendBtn = document.getElementById('sendBtn');
const voiceBtn = document.getElementById('voiceBtn');
const modeSelect = document.getElementById('modeSelect');
const ieltsPartSelector = document.getElementById('ieltsPartSelector');
const ieltsPartSelect = document.getElementById('ieltsPartSelect');
const outputModeSelect = document.getElementById('outputModeSelect');
const getTopicBtn = document.getElementById('getTopicBtn');
const clearHistoryBtn = document.getElementById('clearHistoryBtn');
const newChatBtn = document.getElementById('newChatBtn');
const recordingModal = document.getElementById('recordingModal');
const stopRecordingBtn = document.getElementById('stopRecordingBtn');
const historyList = document.getElementById('historyList');
const refreshHistoryBtn = document.getElementById('refreshHistoryBtn');

// 状态
let isRecording = false;
let mediaRecorder = null;
let audioChunks = [];
let initialized = false;
let currentSessionId = null;

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    initializeEventListeners();
    initializeApp();
});

// 初始化事件监听器
function initializeEventListeners() {
    // 发送按钮
    sendBtn.addEventListener('click', sendMessage);

    // 输入框
    messageInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    // 自动调整输入框高度
    messageInput.addEventListener('input', () => {
        messageInput.style.height = 'auto';
        messageInput.style.height = Math.min(messageInput.scrollHeight, 200) + 'px';
    });

    // 语音按钮
    voiceBtn.addEventListener('click', toggleRecording);

    // 停止录音按钮
    stopRecordingBtn.addEventListener('click', stopRecording);

    // 模式选择
    modeSelect.addEventListener('change', handleModeChange);

    // 获取话题按钮
    getTopicBtn.addEventListener('click', getNewTopic);

    // 清空历史按钮
    clearHistoryBtn.addEventListener('click', clearHistory);

    // 新对话按钮
    newChatBtn.addEventListener('click', startNewChat);

    // 刷新历史按钮
    refreshHistoryBtn.addEventListener('click', loadHistoryList);

    // 初始化时加载历史记录
    loadHistoryList();
}

// 初始化应用
async function initializeApp() {
    try {
        const mode = modeSelect.value;
        const ieltsPart = ieltsPartSelect.value;

        const response = await fetch(`${API_BASE}/api/init`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ mode, ielts_part: parseInt(ieltsPart) })
        });

        const data = await response.json();

        if (data.success) {
            initialized = true;
            if (data.topic) {
                displayTopic(data.topic);
            }
        }
    } catch (error) {
        console.error('初始化失败:', error);
        addErrorMessage('连接服务器失败，请刷新页面重试');
    }
}

// 处理模式变化
async function handleModeChange() {
    const mode = modeSelect.value;
    const ieltsPart = ieltsPartSelect.value;
    
    // 显示/隐藏雅思部分选择器
    if (mode === 'ielts') {
        ieltsPartSelector.style.display = 'block';
        getTopicBtn.style.display = 'block';
    } else {
        ieltsPartSelector.style.display = 'none';
        getTopicBtn.style.display = 'none';
    }
    
    // 重新初始化
    await initializeApp();
}

// 发送消息
async function sendMessage() {
    const message = messageInput.value.trim();
    if (!message) return;

    // 清空输入框
    messageInput.value = '';
    messageInput.style.height = 'auto';

    // 禁用发送按钮
    setSendingState(true);

    // 显示用户消息
    addUserMessage(message);

    // 显示 AI 思考状态
    const loadingMessageId = addLoadingMessage();

    try {
        const outputMode = outputModeSelect.value;
        const useSearch = null; // 自动判断

        const response = await fetch(`${API_BASE}/api/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message,
                use_search: useSearch,
                session_id: currentSessionId || null  // 传递当前会话 ID（可能为 null）
            })
        });

        const data = await response.json();

        // 移除加载消息
        removeMessage(loadingMessageId);

        if (data.success) {
            // 更新当前会话 ID（如果是第一次发送消息）
            if (data.session_id) {
                currentSessionId = data.session_id;
                // 刷新历史记录列表
                loadHistoryList();
            }

            // 显示 AI 回复（包含语法反馈）
            addAIMessage(data.response, data.grammar_feedback);

            // 语音输出
            if (outputMode === 'both' || outputMode === 'voice') {
                playTTS(data.response);
            }
        } else {
            addErrorMessage(data.error || '发送失败，请重试');
        }
    } catch (error) {
        console.error('发送失败:', error);
        removeMessage(loadingMessageId);
        addErrorMessage('网络错误，请重试');
    } finally {
        setSendingState(false);
    }
}

// 添加用户消息
function addUserMessage(text) {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message message-user';
    messageDiv.innerHTML = `
        <div class="message-content">
            <div class="message-avatar">👤</div>
            <div class="message-text">
                <p>${escapeHtml(text)}</p>
            </div>
        </div>
    `;
    messagesContainer.appendChild(messageDiv);
    scrollToBottom();
}

// 添加 AI 消息
function addAIMessage(text, grammarFeedback) {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message message-ai';

    // 处理文本中的换行和格式
    const formattedText = formatMessage(text);
    
    // 如果有语法反馈，添加到消息内部
    let grammarHtml = '';
    if (grammarFeedback) {
        grammarHtml = `
            <div class="grammar-feedback">
                <div class="grammar-feedback-content">
                    <div class="grammar-feedback-title">💡 语法建议</div>
                    <div>${formatMessage(grammarFeedback)}</div>
                </div>
            </div>
        `;
    }

    messageDiv.innerHTML = `
        <div class="message-content">
            <div class="message-avatar">🤖</div>
            <div class="message-text">
                ${formattedText}
            </div>
        </div>
        ${grammarHtml}
    `;
    messagesContainer.appendChild(messageDiv);
    scrollToBottom();
}

// 添加加载消息
function addLoadingMessage() {
    const id = 'loading-' + Date.now();
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message message-ai';
    messageDiv.id = id;
    messageDiv.innerHTML = `
        <div class="message-content">
            <div class="message-avatar">🤖</div>
            <div class="message-text">
                <div class="typing-indicator">
                    <span></span>
                    <span></span>
                    <span></span>
                </div>
            </div>
        </div>
    `;
    messagesContainer.appendChild(messageDiv);
    scrollToBottom();
    return id;
}

// 移除消息
function removeMessage(id) {
    const message = document.getElementById(id);
    if (message) {
        message.remove();
    }
}

// 添加错误消息
function addErrorMessage(text) {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message message-ai';
    messageDiv.innerHTML = `
        <div class="message-content">
            <div class="message-avatar">⚠️</div>
            <div class="message-text">
                <p style="color: var(--danger-color);">${escapeHtml(text)}</p>
            </div>
        </div>
    `;
    messagesContainer.appendChild(messageDiv);
    scrollToBottom();
}

// 显示话题
function displayTopic(topic) {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message message-ai';
    messageDiv.innerHTML = `
        <div class="message-content">
            <div class="message-avatar">📝</div>
            <div class="message-text">
                <div class="topic-card">
                    <div class="topic-card-title">当前雅思话题</div>
                    <div class="topic-card-content">${escapeHtml(topic)}</div>
                </div>
            </div>
        </div>
    `;
    messagesContainer.appendChild(messageDiv);
    scrollToBottom();
}

// 获取新话题
async function getNewTopic() {
    try {
        const response = await fetch(`${API_BASE}/api/topic`, {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (data.success) {
            displayTopic(data.topic);
        }
    } catch (error) {
        console.error('获取话题失败:', error);
        addErrorMessage('获取话题失败，请重试');
    }
}

// 清空历史
async function clearHistory() {
    if (!confirm('确定要清空对话历史吗？')) return;

    try {
        await fetch(`${API_BASE}/api/history/clear`, {
            method: 'POST'
        });

        // 清空消息显示
        messagesContainer.innerHTML = `
            <div class="welcome-message">
                <h2>🎓 欢迎来到 DAMN</h2>
                <p>你的雅思口语练习伙伴</p>
                <div class="features">
                    <div class="feature-item">
                        <span class="feature-icon">🎤</span>
                        <span>语音输入</span>
                    </div>
                    <div class="feature-item">
                        <span class="feature-icon">🔊</span>
                        <span>语音输出</span>
                    </div>
                    <div class="feature-item">
                        <span class="feature-icon">📚</span>
                        <span>雅思话题</span>
                    </div>
                    <div class="feature-item">
                        <span class="feature-icon">🔍</span>
                        <span>联网搜索</span>
                    </div>
                    <div class="feature-item">
                        <span class="feature-icon">💡</span>
                        <span>语法纠正</span>
                    </div>
                </div>
            </div>
        `;
    } catch (error) {
        console.error('清空历史失败:', error);
    }
}

// ==================== 历史记录功能 ====================

// 加载历史记录列表
async function loadHistoryList() {
    try {
        const response = await fetch(`${API_BASE}/api/sessions?limit=50`);
        const data = await response.json();

        if (data.success) {
            renderHistoryList(data.sessions);
        }
    } catch (error) {
        console.error('加载历史记录失败:', error);
    }
}

// 渲染历史记录列表
function renderHistoryList(sessions) {
    if (!sessions || sessions.length === 0) {
        historyList.innerHTML = '<div class="history-empty">暂无历史记录</div>';
        return;
    }

    historyList.innerHTML = sessions.map(session => {
        const date = new Date(session.updated_at || session.created_at);
        const dateStr = `${date.getMonth() + 1}/${date.getDate()} ${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`;
        const isActive = session.id === currentSessionId;

        return `
            <div class="history-item ${isActive ? 'active' : ''}" data-session-id="${session.id}">
                <div class="history-item-title">${escapeHtml(session.title)}</div>
                <div class="history-item-meta">
                    <span>${session.mode === 'ielts' ? '📚' : '💬'} ${dateStr}</span>
                </div>
                <button class="history-item-delete" data-session-id="${session.id}" title="删除">🗑️</button>
            </div>
        `;
    }).join('');

    // 绑定点击事件
    historyList.querySelectorAll('.history-item').forEach(item => {
        item.addEventListener('click', (e) => {
            if (!e.target.classList.contains('history-item-delete')) {
                const sessionId = parseInt(item.dataset.sessionId);
                loadSession(sessionId);
            }
        });
    });

    // 绑定删除事件
    historyList.querySelectorAll('.history-item-delete').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            const sessionId = parseInt(btn.dataset.sessionId);
            deleteSession(sessionId);
        });
    });
}

// 加载会话
async function loadSession(sessionId) {
    try {
        const response = await fetch(`${API_BASE}/api/sessions/load`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ session_id: sessionId })
        });

        const data = await response.json();

        if (data.success) {
            currentSessionId = sessionId;

            // 更新模式选择器
            modeSelect.value = data.session.mode;
            ieltsPartSelect.value = data.session.ielts_part || 1;

            // 显示/隐藏雅思部分选择器
            if (data.session.mode === 'ielts') {
                ieltsPartSelector.style.display = 'block';
                getTopicBtn.style.display = 'block';
            } else {
                ieltsPartSelector.style.display = 'none';
                getTopicBtn.style.display = 'none';
            }

            // 清空并显示消息
            messagesContainer.innerHTML = '';

            // 显示话题（如果有）
            if (data.session.topic) {
                displayTopic(data.session.topic);
            }

            // 显示历史消息
            data.messages.forEach(msg => {
                if (msg.role === 'user') {
                    addUserMessage(msg.content);
                } else {
                    addAIMessage(msg.content, msg.grammar_feedback);
                }
            });

            // 刷新历史记录列表
            loadHistoryList();
        }
    } catch (error) {
        console.error('加载会话失败:', error);
        addErrorMessage('加载会话失败，请重试');
    }
}

// 删除会话
async function deleteSession(sessionId) {
    if (!confirm('确定要删除这个历史记录吗？')) return;

    try {
        await fetch(`${API_BASE}/api/sessions/${sessionId}`, {
            method: 'DELETE'
        });

        // 如果删除的是当前会话，创建新会话
        if (sessionId === currentSessionId) {
            currentSessionId = null;
            messagesContainer.innerHTML = `
                <div class="welcome-message">
                    <h2>🎓 欢迎来到 DAMN</h2>
                    <p>你的雅思口语练习伙伴</p>
                    <div class="features">
                        <div class="feature-item">
                            <span class="feature-icon">🎤</span>
                            <span>语音输入</span>
                        </div>
                        <div class="feature-item">
                            <span class="feature-icon">🔊</span>
                            <span>语音输出</span>
                        </div>
                        <div class="feature-item">
                            <span class="feature-icon">📚</span>
                            <span>雅思话题</span>
                        </div>
                        <div class="feature-item">
                            <span class="feature-icon">🔍</span>
                            <span>联网搜索</span>
                        </div>
                        <div class="feature-item">
                            <span class="feature-icon">💡</span>
                            <span>语法纠正</span>
                        </div>
                    </div>
                </div>
            `;
        }

        // 刷新历史记录列表
        loadHistoryList();
    } catch (error) {
        console.error('删除会话失败:', error);
    }
}

// 开始新对话
async function startNewChat() {
    // 通知后端重置会话
    try {
        await fetch(`${API_BASE}/api/sessions/reset`, {
            method: 'POST'
        });
    } catch (error) {
        console.error('重置会话失败:', error);
    }

    // 只重置会话 ID，不创建新会话
    currentSessionId = null;

    // 清空消息显示
    messagesContainer.innerHTML = `
        <div class="welcome-message">
            <h2>🎓 欢迎来到 DAMN</h2>
            <p>你的雅思口语练习伙伴</p>
            <div class="features">
                <div class="feature-item">
                    <span class="feature-icon">🎤</span>
                    <span>语音输入</span>
                </div>
                <div class="feature-item">
                    <span class="feature-icon">🔊</span>
                    <span>语音输出</span>
                </div>
                <div class="feature-item">
                    <span class="feature-icon">📚</span>
                    <span>雅思话题</span>
                </div>
                <div class="feature-item">
                    <span class="feature-icon">🔍</span>
                    <span>联网搜索</span>
                </div>
                <div class="feature-item">
                    <span class="feature-icon">💡</span>
                    <span>语法纠正</span>
                </div>
            </div>
        </div>
    `;
}

// 语音录制
async function toggleRecording() {
    if (isRecording) {
        stopRecording();
    } else {
        startRecording();
    }
}

async function startRecording() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        
        mediaRecorder = new MediaRecorder(stream);
        audioChunks = [];
        
        mediaRecorder.ondataavailable = (event) => {
            audioChunks.push(event.data);
        };
        
        mediaRecorder.onstop = async () => {
            const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
            await sendVoiceMessage(audioBlob);
            
            // 停止所有音轨
            stream.getTracks().forEach(track => track.stop());
        };
        
        mediaRecorder.start();
        isRecording = true;
        voiceBtn.classList.add('recording');
        recordingModal.style.display = 'flex';
    } catch (error) {
        console.error('录音失败:', error);
        addErrorMessage('无法访问麦克风，请检查权限设置');
    }
}

function stopRecording() {
    if (mediaRecorder && isRecording) {
        mediaRecorder.stop();
        isRecording = false;
        voiceBtn.classList.remove('recording');
        recordingModal.style.display = 'none';
    }
}

async function sendVoiceMessage(audioBlob) {
    // 显示录音成功消息
    addUserMessage('🎤 [语音消息]');
    
    // 显示 AI 思考状态
    const loadingMessageId = addLoadingMessage();
    
    try {
        const formData = new FormData();
        formData.append('audio', audioBlob, 'recording.wav');
        
        // 语音识别
        const transcribeResponse = await fetch(`${API_BASE}/api/transcribe`, {
            method: 'POST',
            body: formData
        });
        
        const transcribeData = await transcribeResponse.json();
        
        if (!transcribeData.success) {
            throw new Error('语音识别失败');
        }
        
        const text = transcribeData.text;
        
        // 更新用户消息为识别的文字
        const lastUserMessage = messagesContainer.querySelector('.message-user:last-child');
        if (lastUserMessage) {
            lastUserMessage.querySelector('.message-text').innerHTML = `<p>${escapeHtml(text)}</p>`;
        }
        
        // 发送文字聊天
        const outputMode = outputModeSelect.value;
        
        const chatResponse = await fetch(`${API_BASE}/api/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: text })
        });
        
        const chatData = await chatResponse.json();
        
        // 移除加载消息
        removeMessage(loadingMessageId);
        
        if (chatData.success) {
            // 显示 AI 回复
            addAIMessage(chatData.response);
            
            // 显示语法反馈
            if (chatData.grammar_feedback) {
                showGrammarFeedback(chatData.grammar_feedback);
            }
            
            // 语音输出
            if (outputMode === 'both' || outputMode === 'voice') {
                playTTS(chatData.response);
            }
        } else {
            addErrorMessage(chatData.error || '发送失败，请重试');
        }
    } catch (error) {
        console.error('语音处理失败:', error);
        removeMessage(loadingMessageId);
        addErrorMessage('语音处理失败，请重试');
    }
}

// 播放 TTS
async function playTTS(text) {
    try {
        const response = await fetch(`${API_BASE}/api/tts`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text })
        });
        
        const data = await response.json();

        if (data.success && data.audio_url) {
            const audio = new Audio(data.audio_url);
            audio.play();
        }
    } catch (error) {
        console.error('TTS 播放失败:', error);
    }
}

// 设置发送状态
function setSendingState(isSending) {
    sendBtn.disabled = isSending;
    messageInput.disabled = isSending;
}

// 滚动到底部
function scrollToBottom() {
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

// HTML 转义
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// 格式化消息
function formatMessage(text) {
    // 处理换行
    let formatted = escapeHtml(text);
    formatted = formatted.replace(/\n/g, '<br>');
    
    // 处理列表
    formatted = formatted.replace(/^[•\-\*]\s+(.+)/gm, '<li>$1</li>');
    formatted = formatted.replace(/(<li>.*<\/li>\n?)+/g, '<ul style="margin: 8px 0; padding-left: 20px;">$&</ul>');
    
    return `<p>${formatted}</p>`;
}
