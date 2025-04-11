document.addEventListener("DOMContentLoaded", () => {
    try {
        // 获取当前页面路径
        const currentPage = window.location.pathname.split('/').pop();

        // 只在首页初始化特定模块
        if (currentPage === 'index.html' || currentPage === '') {
            initChatModule();
            initImageUploadModule();
            initBirdFactModule();
            initSpeechRecognitionModule();  // 初始化语音识别模块
        }

        // 通用初始化（所有页面都需要）
        initTheme();
        initBirdFactModule();
    } catch (error) {
        console.error("初始化失败:", error);
        // 更友好的错误处理
        const errorElement = document.getElementById('error-message') || document.body;
        errorElement.innerHTML = `<div class="error-notice">系统初始化遇到问题，请刷新页面或稍后再试</div>`;
    }
});

// 初始化主题（通用函数）
function initTheme() {
    let currentTheme = localStorage.getItem('theme') || 'light'; // 默认 'light' 模式
    applyTheme(currentTheme); // 调用 applyTheme 来应用主题

    // 监听主题切换按钮
    const themeToggle = document.getElementById("themeToggle");
    if (themeToggle) {
        themeToggle.addEventListener("click", () => {
            currentTheme = currentTheme === "light" ? "dark" : "light";
            localStorage.setItem('theme', currentTheme); // 存储当前主题
            applyTheme(currentTheme); // 重新应用主题
        });
    }
}

function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    // 设置背景图片
    const body = document.body;
    if (theme === 'dark') {
        body.style.backgroundImage = 'url("/static/images/05_dark.png")'; // 替换为你希望的暗色背景图片
        body.style.backgroundSize = 'cover';
    } else {
        body.style.backgroundImage = 'url("/static/images/05.png")'; // 替换为你希望的亮色背景图片
        body.style.backgroundSize = 'cover';
    }
}

// 通用工具函数
function getElementOrThrow(id) {
    const element = document.getElementById(id);
    if (!element) throw new Error(`未找到元素: ${id}`);
    return element;
}

// 图片检测模块专用的safeFetch，不需要流式处理
async function safeFetchImageDetection(url, options) {
    try {
        const response = await fetch(url, options);
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error("请求出错:", error);
        throw error;
    }
}

// 智能体问答模块专用的safeFetch，支持流式响应
async function safeFetchChat(url, options) {
    try {
        const response = await fetch(url, options);
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        return response;
    } catch (error) {
        console.error("请求出错:", error);
        throw error;
    }
}

// 初始化智能体问答模块
function initChatModule() {
    const elements = {
        chatBox: getElementOrThrow("chatBox"),
        inputField: getElementOrThrow("question"),
        sendButton: getElementOrThrow("sendBtn")
    };

    // 恢复历史聊天记录
    const history = JSON.parse(localStorage.getItem("chatHistory") || "[]");
    for (const { sender, text } of history) {
        const messageDiv = document.createElement("div");
        messageDiv.className = `message ${sender}-message`;
        messageDiv.textContent = sanitizeInput(text);
        elements.chatBox.appendChild(messageDiv);
    }
    elements.chatBox.scrollTop = elements.chatBox.scrollHeight;

    elements.sendButton.addEventListener("click", handleSendMessage);
    elements.inputField.addEventListener("keydown", (e) => {
        if (e.key === "Enter") {
            e.preventDefault();
            handleSendMessage();
        }
    });

    let accumulatedText = '';  // 用来积累文本

    async function handleSendMessage() {
        const question = elements.inputField.value.trim();
        if (!question) return;

        addMessage(question, "user");
        elements.inputField.value = "";

        const sendIcon = document.getElementById("sendIcon");
        if (sendIcon) {
            sendIcon.innerHTML = '⏳';
            sendIcon.classList.add('thinking-icon');
        }

        const loadingMsg = addMessage("🤖 正在思考中...", "bot");

        try {
            const response = await safeFetchChat("http://localhost:11434/api/generate", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    model: "deepseek-r1:1.5b",
                    prompt: question,
                    stream: true
                })
            });

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let done = false;
            let text = '';
            let lastText = '';

            while (!done) {
                const { value, done: doneReading } = await reader.read();
                done = doneReading;

                if (value) {
                    const chunk = decoder.decode(value, { stream: true });
                    const jsonObjects = chunk.split('\n').filter(Boolean);

                    jsonObjects.forEach(jsonObject => {
                        const parsed = JSON.parse(jsonObject);
                        if (parsed.response) {
                            text += parsed.response;

                            const rendered = DOMPurify.sanitize(marked.parse(text));
                            loadingMsg.innerHTML = rendered;

                            const newText = text.slice(lastText.length);

                            if (newText) {
                                accumulatedText += newText;

                                clearTimeout(window.textTimeout);
                                window.textTimeout = setTimeout(() => {
                                    queueSpeech(accumulatedText);
                                    accumulatedText = '';
                                }, 1000);
                                lastText = text;
                            }

                            elements.chatBox.scrollTop = elements.chatBox.scrollHeight;
                        }
                    });
                }
            }
        } catch (error) {
            loadingMsg.textContent = `错误: ${error.message}`;
            console.error("消息发送失败:", error);
        } finally {
            if (sendIcon) {
                sendIcon.innerHTML = '🚀';
                sendIcon.classList.remove('thinking-icon');
            }
        }
    }

    // 添加语音播报队列
    const speechQueue = [];
    let isSpeaking = false;

    function queueSpeech(text) {
        speechQueue.push(text);
        if (!isSpeaking) {
            playNextSpeech();
        }
    }

    function playNextSpeech() {
        if (speechQueue.length === 0) {
            isSpeaking = false;
            return;
        }

        isSpeaking = true;
        const nextText = speechQueue.shift();

        const utterance = new SpeechSynthesisUtterance(nextText);
        utterance.lang = 'zh-CN';
        utterance.rate = 1.2;
        utterance.pitch = 1;
        utterance.volume = 1;

        utterance.onend = () => {
            playNextSpeech(); // 播完继续下一个
        };

        speechSynthesis.speak(utterance);
    }

    function speakText(text) {
        if (window.audioPlayer && typeof audioPlayer.postMessage === 'function') {
            // 使用讯飞流式播报
            // 假设你已经有了 audioPlayer 实例，并处理 base64 音频
            // 你可以在这里请求后端获取合成结果，然后播放
        } else {
            // 使用浏览器内置语音作为备选
            const speech = new SpeechSynthesisUtterance(text);
            speech.lang = 'zh-CN';
            speech.rate = 1.2;
            speech.pitch = 1;
            speech.volume = 1;
            window.speechSynthesis.speak(speech);
        }
    }

    function sanitizeInput(text) {
    return text.toString().replace(/</g, "&lt;").replace(/>/g, "&gt;");
}


    function addMessage(text, sender) {
        const messageDiv = document.createElement("div");
        messageDiv.className = `message ${sender}-message`;
        messageDiv.textContent = sanitizeInput(text);
        elements.chatBox.appendChild(messageDiv);
        elements.chatBox.scrollTop = elements.chatBox.scrollHeight;

        // 保存到 localStorage
        const stored = JSON.parse(localStorage.getItem("chatHistory") || "[]");
        stored.push({ sender, text });
        localStorage.setItem("chatHistory", JSON.stringify(stored));

        // ✅ 如果是 AI 助手的回复，就朗读
        if (sender === "bot" && text.trim()) {
            speakText(text);
        }

        return messageDiv;
    }
}
function initSpeechRecognitionModule() {
    const elements = {
        startBtn: document.getElementById("recordBtn"),
        resultBox: document.getElementById("question")
    };

    const wsUrl = "ws://127.0.0.1:8000/ws/speech";
    let websocket = null;
    let audioContext = null;
    let processor = null;
    let micStream = null;

    let isRecording = false;

    elements.startBtn.addEventListener("click", async () => {
        if (!isRecording) {
            await startWebSocket();
            elements.startBtn.textContent = "⏹️";
        } else {
            stopRecording();
            elements.startBtn.textContent = "🎤";
        }
        isRecording = !isRecording;
    });

    async function startWebSocket() {
        websocket = new WebSocket(wsUrl);

        websocket.binaryType = "arraybuffer";

        websocket.onopen = async () => {
            console.log("WebSocket 已连接");
            await startRecording();
        };

        websocket.onmessage = (event) => {
            console.log("识别结果：", event.data);
            elements.resultBox.value = event.data;
        };

        websocket.onerror = (err) => {
            console.error("WebSocket 错误:", err);
        };

        websocket.onclose = () => {
            console.log("WebSocket 已关闭");
        };
    }

    async function startRecording() {
        audioContext = new (window.AudioContext || window.webkitAudioContext)({
            sampleRate: 16000  // 设置采样率为 16000Hz，符合讯飞要求
        });

        micStream = await navigator.mediaDevices.getUserMedia({ audio: true });
        const source = audioContext.createMediaStreamSource(micStream);

        processor = audioContext.createScriptProcessor(4096, 1, 1);

        processor.onaudioprocess = function (e) {
            const input = e.inputBuffer.getChannelData(0);
            const pcm = floatTo16BitPCM(input);
            if (websocket.readyState === WebSocket.OPEN) {
                websocket.send(pcm);
            }
        };

        source.connect(processor);
        processor.connect(audioContext.destination);
    }

    function stopRecording() {
        if (processor) processor.disconnect();
        if (audioContext) audioContext.close();
        if (micStream) {
            micStream.getTracks().forEach(track => track.stop());
        }
        if (websocket && websocket.readyState === WebSocket.OPEN) {
            websocket.close();
        }
    }

    // 把 Float32 ([-1.0, 1.0]) 转为 Int16 PCM
    function floatTo16BitPCM(input) {
        const output = new DataView(new ArrayBuffer(input.length * 2));
        for (let i = 0; i < input.length; i++) {
            let s = Math.max(-1, Math.min(1, input[i]));
            output.setInt16(i * 2, s < 0 ? s * 0x8000 : s * 0x7FFF, true);
        }
        return output.buffer;
    }
}


// 初始化图片上传模块
function initImageUploadModule() {
    const elements = {
        imageUpload: getElementOrThrow("imageUpload"),
        videoUpload: getElementOrThrow("videoUpload"),
        uploadPreview: getElementOrThrow("uploadPreview"),
        resultContainer: getElementOrThrow("resultContainer"),
        processingOverlay: getElementOrThrow("processing"),
        detectedObjectsList: getElementOrThrow("detectedObjects"),
        wikiInfoContainer: getElementOrThrow("wikiInfoContainer")
    };

    const lastDetection = JSON.parse(localStorage.getItem("lastDetection"));
    if (lastDetection) {
        displayDetectionResults(lastDetection, elements);
        displayProcessedImage(lastDetection.id, elements);
    }

    elements.imageUpload.addEventListener("change", handleImageSelection);
    elements.videoUpload.addEventListener("change", handleVideoSelection);

    async function handleImageSelection(event) {
        const file = event.target.files[0];
        if (!file) return;

        // 图片格式验证：检查文件类型是否为图片
        if (!file.type.startsWith('image/')) {
            alert('请上传有效的图片文件！');
            return;
        }

        // 如果是图片，则继续进行上传和处理
        elements.processingOverlay.style.display = "grid";
        elements.detectedObjectsList.innerHTML = "";

        try {
            const objectUrl = URL.createObjectURL(file);
            elements.uploadPreview.style.backgroundImage = `url(${objectUrl})`;
            elements.uploadPreview.onload = () => URL.revokeObjectURL(objectUrl);

            const formData = new FormData();
            formData.append("file", file);

            const response = await safeFetchImageDetection("http://127.0.0.1:8000/yolo/upload", {
                method: "POST",
                body: formData
            });

            displayDetectionResults(response, elements);
            await displayProcessedImage(response.id, elements);
        } catch (error) {
            console.error("图片处理失败:", error);
            alert(`图片处理失败: ${error.message}`);
        } finally {
            elements.processingOverlay.style.display = "none";
        }
    }

    async function handleVideoSelection(event) {
        const file = event.target.files[0];
        if (!file) return;

        // 视频格式验证：检查文件类型是否为视频
        if (!file.type.startsWith('video/')) {
            alert('请上传有效的视频文件！');
            return;
        }

        elements.processingOverlay.style.display = "grid";
        elements.detectedObjectsList.innerHTML = "";

        try {
            const objectUrl = URL.createObjectURL(file);
            const video = document.createElement('video');
            video.src = objectUrl;
            video.controls = true;
            video.style.maxWidth = '100%';
            elements.uploadPreview.innerHTML = '';
            elements.uploadPreview.appendChild(video);

            const formData = new FormData();
            formData.append("file", file);

            // 使用fetch API进行流式请求
            const response = await fetch('http://127.0.0.1:8000/yolo/upload/video', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const reader = response.body.getReader();
            const decoder = new TextDecoder();

            // 创建画布用于显示处理后的帧
            const canvas = document.createElement('canvas');
            canvas.style.maxWidth = '100%';
            elements.resultContainer.innerHTML = '';
            
            // Create a single image element for frame updates
            const frameImg = document.createElement('img');
            frameImg.style.maxWidth = '100%';
            elements.resultContainer.appendChild(frameImg);

            // 处理流式数据
            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                // 解码数据
                const chunk = decoder.decode(value, { stream: true });
                const lines = chunk.split('\n');

                for (const line of lines) {
                    if (!line || !line.startsWith('data:')) continue;

                    try {
                        const data = JSON.parse(line.slice(5));
                        
                        if (data.error) {
                            throw new Error(data.error);
                        }

                        // 更新检测到的标签
                        if (data.labels && data.labels.length > 0) {
                            elements.detectedObjectsList.innerHTML = data.labels
                                .map(label => `<li>${label}</li>`)
                                .join("");
                        } else {
                            elements.detectedObjectsList.innerHTML = "<li>未检测到对象</li>";
                        }

                        // 显示处理后的帧
                        if (data.frame_id) {
                            frameImg.src = `http://127.0.0.1:8000/yolo/download/video/${data.frame_id}`;
                        }
                    } catch (error) {
                        console.error("处理视频帧失败:", error);
                        elements.detectedObjectsList.innerHTML = `<li>处理失败: ${error.message}</li>`;
                    }
                }
            }

        } catch (error) {
            console.error("视频处理失败:", error);
            alert(`视频处理失败: ${error.message}`);
        } finally {
            elements.processingOverlay.style.display = "none";
        }
    }

    function displayVideoResults(response) {
        localStorage.setItem("lastDetection", JSON.stringify(response));
        const detectedObjectsList = getElementOrThrow("detectedObjects");
        detectedObjectsList.innerHTML = "";

        if (response.unique_labels && response.unique_labels.length > 0) {
            // 显示所有检测到的标签
            detectedObjectsList.innerHTML = response.unique_labels
                .map(label => `<li>${label}</li>`)
                .join("");

            // 显示视频帧
            elements.resultContainer.innerHTML = "";
            const frameContainer = document.createElement('div');
            frameContainer.className = 'video-frames';
            frameContainer.style.display = 'grid';
            frameContainer.style.gridTemplateColumns = 'repeat(auto-fill, minmax(200px, 1fr))';
            frameContainer.style.gap = '10px';

            // 加载前5帧作为预览
            const previewFrames = response.frame_ids.slice(0, 5);
            previewFrames.forEach(frameId => {
                const frameImg = document.createElement('img');
                frameImg.src = `http://127.0.0.1:8000/yolo/download/video/${frameId}`;
                frameImg.alt = `Frame ${frameId}`;
                frameImg.style.width = '100%';
                frameImg.style.height = 'auto';
                frameContainer.appendChild(frameImg);
            });

            elements.resultContainer.appendChild(frameContainer);
        } else {
            detectedObjectsList.innerHTML = "<li>未检测到对象</li>";
            elements.resultContainer.innerHTML = "";
        }
    }

    function displayDetectionResults(response, elements) {
        localStorage.setItem("lastDetection", JSON.stringify(response));
        elements.detectedObjectsList.innerHTML = "";

        if (response.labels && response.labels.length > 0) {
            elements.detectedObjectsList.innerHTML = response.labels
                .map(label => `<li>${label}</li>`)
                .join("");

            if (response.wiki_info) {
                const wikiInfo = response.wiki_info;
                elements.wikiInfoContainer.innerHTML =
                    `<h3>关于 ${wikiInfo.title || '鸟类'}</h3>
                    <p>${wikiInfo.summary || "暂无介绍"}</p>
                    ${wikiInfo.image ? `<img src="${wikiInfo.image}" alt="鸟类图片" style="max-width:200px;">` : ""}
                    <p><a href="${wikiInfo.wiki_url}" target="_blank">查看更多</a></p>`;
            } else {
                elements.wikiInfoContainer.innerHTML = "<p>未找到相关 Wikipedia 介绍。</p>";
            }
        } else {
            elements.detectedObjectsList.innerHTML = "<li>未检测到对象</li>";
            elements.wikiInfoContainer.innerHTML = "";
        }
    }

    async function displayProcessedImage(imageId, elements) {
        try {
            const imageResponse = await fetch(`http://127.0.0.1:8000/yolo/download/${imageId}`);
            if (!imageResponse.ok) {
                throw new Error(`获取处理后的图片失败: ${imageResponse.status}`);
            }

            const imageBlob = await imageResponse.blob();
            const processedImageUrl = URL.createObjectURL(imageBlob);

            const processedImg = document.createElement("img");
            processedImg.src = processedImageUrl;
            processedImg.alt = "处理后的图片";
            processedImg.style.maxWidth = "100%";

            elements.resultContainer.innerHTML = "";
            elements.resultContainer.appendChild(processedImg);

            processedImg.onload = () => URL.revokeObjectURL(processedImageUrl);
        } catch (error) {
            console.error("显示处理图片失败:", error);
            elements.resultContainer.innerHTML = "<p>无法显示处理后的图片</p>";
        }
    }
}

// 初始化鸟类趣闻模块
function initBirdFactModule() {
    const factBox = document.getElementById("factBox");
    const factContainer = document.querySelector(".fact-container");

    if (!factBox || !factContainer) {
        console.warn('鸟类趣闻模块元素未找到');
        return;
    }

    const facts = [
        "天鹅可以一辈子与同伴保持伴侣关系。",
        "鸽子能够辨认出不同的画作。",
        "鹰的视力是人类的8倍。",
        "鸵鸟的眼睛比大脑还要大。",
        "蜂鸟的心跳每分钟超过 1,200 次。",
        "蜂鸟是世界上唯一能倒着飞的鸟。",
        "企鹅能在水下憋气超过 20 分钟。",
        "渡鸦能模仿人类的声音！",
        "猫头鹰没有眼球，它们的眼睛是管状的。",
        "喜鹊是少数能认出自己在镜子里的鸟类。",
        "信鸽的归巢能力极强，可以找到千里之外的家。",
        "鹦鹉不仅能模仿人类说话，还能学习不同口音！"
    ];

    const birdImages = [
        "/static/images/01.jpg",
        "/static/images/02.jpg",
        "/static/images/03.jpg",
        "/static/images/04.png",
        "/static/images/05.png",
        "/static/images/06.png"
    ];

    const updateFact = () => {
        if (factBox) {
            factBox.textContent = facts[Math.floor(Math.random() * facts.length)];
        }
    };

    const changeBackground = () => {
        if (factContainer) {
            const randomImage = birdImages[Math.floor(Math.random() * birdImages.length)];
            factContainer.style.backgroundImage = `url(${randomImage})`;
        }
    };

    // 初始化执行
    updateFact();
    changeBackground();

    // 设置定时器
    const factInterval = setInterval(updateFact, 30000);
    const bgInterval = setInterval(changeBackground, 30000);

    // 返回清理函数
    return () => {
        clearInterval(factInterval);
        clearInterval(bgInterval);
    };
}

function openPopup(id) {
    document.getElementById(id).style.display = "flex";
    if (id === "videoPopup") {
        switchVideoMode('camera'); // 默认进入摄像头模式
    }
}


function closePopup(id) {
    document.getElementById(id).style.display = "none";  // 隐藏弹窗
}

function switchVideoMode(mode) {
    const cameraBox = document.getElementById("cameraBox");
    const uploadBox = document.getElementById("uploadBox");
    const cameraBtn = document.getElementById("cameraModeBtn");
    const uploadBtn = document.getElementById("uploadModeBtn");

    // 停掉前一个视频
    stopAllVideo();

    if (mode === 'camera') {
        cameraBox.style.display = "block";
        uploadBox.style.display = "none";
        cameraBtn.classList.add("active");
        uploadBtn.classList.remove("active");

        // 开启摄像头
        navigator.mediaDevices.getUserMedia({ video: true })
            .then(stream => {
                const video = document.getElementById("cameraVideo");
                video.srcObject = stream;
            })
            .catch(err => {
                alert("无法访问摄像头：" + err.message);
            });

    } else if (mode === 'upload') {
        cameraBox.style.display = "none";
        uploadBox.style.display = "block";
        cameraBtn.classList.remove("active");
        uploadBtn.classList.add("active");
    }
}

function stopAllVideo() {
    // 停止摄像头
    const cameraVideo = document.getElementById("cameraVideo");
    if (cameraVideo.srcObject) {
        cameraVideo.srcObject.getTracks().forEach(track => track.stop());
        cameraVideo.srcObject = null;
    }

    // 停止上传的视频
    const uploadedVideo = document.getElementById("uploadedVideo");
    uploadedVideo.pause();
    uploadedVideo.removeAttribute("src");
    uploadedVideo.load();
}

// 上传视频播放逻辑
const videoUploadElement = document.getElementById("videoUpload");
if (videoUploadElement) {
    videoUploadElement.addEventListener("change", function () {
        const file = this.files[0];
        if (file) {
            const url = URL.createObjectURL(file);
            const video = document.getElementById("uploadedVideo");
            if (video) {
                video.src = url;
                video.play();
            }
        }
    });
}

//历史记录
function renderHistoryData(dataArray) {
    const tbody = document.getElementById("historyTableBody");
    tbody.innerHTML = ""; // 清空旧数据

    dataArray.forEach(item => {
        const row = document.createElement("tr");

        row.innerHTML = `
            <td>${item.time}</td>
            <td>${item.target}</td>
            <td>${item.result}</td>
            <td>${item.confidence}</td>
            <td>${item.warning ? '是' : '否'}</td>
        `;

        tbody.appendChild(row);
    });
}

//数据看板
function updateDashboard(data) {
    document.getElementById("totalCount").textContent = data.total || 0;
    document.getElementById("todayCount").textContent = data.today || 0;
    document.getElementById("warningCount").textContent = data.warnings || 0;
    document.getElementById("todayWarningCount").textContent = data.todayWarnings || 0;
    document.getElementById("qaCount").textContent = data.qa || 0;

    // 你可以用图表库（如 ECharts）来渲染 chart-placeholder
    renderChart(data.chartData || []);
}

//异常预警
function updateAlerts(alerts) {
    const list = document.getElementById("alertList");
    list.innerHTML = ""; // 清空旧内容

    if (alerts.length === 0) {
        list.innerHTML = "<p>暂无异常预警信息。</p>";
        return;
    }

    alerts.forEach(item => {
        const card = document.createElement("div");
        card.className = "alert-card";

        card.innerHTML = `
            <img src="${item.image}" alt="预警图像" width="100">
            <div>
                <p>时间：${item.time}</p>
                <p>类型：${item.type}</p>
                <p>等级：${item.level}</p>
            </div>
        `;
        list.appendChild(card);
    });
}

//监听阈值变化（实时传给后端）
document.getElementById("thresholdInput").addEventListener("change", function () {
    const threshold = parseFloat(this.value);
    if (!isNaN(threshold)) {
        // 可发送到后端 API
        console.log("设置新的阈值：", threshold);
        // fetch('/api/set-threshold', { method: 'POST', body: JSON.stringify({ threshold }) });
    }
});

