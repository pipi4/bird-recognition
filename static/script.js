document.addEventListener("DOMContentLoaded", () => {
    try {
        // 获取当前页面路径
        const currentPage = window.location.pathname.split('/').pop();

        // 只在首页初始化特定模块
        if (currentPage === 'index.html' || currentPage === '') {
            initChatModule();
            initImageUploadModule();
            initBirdFactModule();
        }

        // 通用初始化（所有页面都需要）
        initTheme();
    } catch (error) {
        console.error("初始化失败:", error);
        // 更友好的错误处理
        const errorElement = document.getElementById('error-message') || document.body;
        errorElement.innerHTML = `<div class="error-notice">系统初始化遇到问题，请刷新页面或稍后再试</div>`;
    }
});

// 初始化主题（通用函数）
function initTheme() {
    let currentTheme = localStorage.getItem('theme') || 'light';
    applyTheme(currentTheme);

    const themeToggle = document.getElementById("themeToggle");
    if (themeToggle) {
        themeToggle.addEventListener("click", () => {
            currentTheme = currentTheme === "light" ? "dark" : "light";
            localStorage.setItem('theme', currentTheme);
            applyTheme(currentTheme);
        });
    }
}

function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
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

    elements.sendButton.addEventListener("click", handleSendMessage);
    elements.inputField.addEventListener("keydown", (e) => {
        if (e.key === "Enter") {
            e.preventDefault();
            handleSendMessage();
        }
    });

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

        const loadingMsg = addMessage("🤖 思考中...", "bot");

        try {
            const response = await safeFetchChat("http://127.0.0.1:8000/deepseek/ask", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ question })
            });

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let done = false;
            let text = '';

            while (!done) {
                const { value, done: doneReading } = await reader.read();
                done = doneReading;
                text += decoder.decode(value, { stream: true });
                loadingMsg.textContent = text;
                elements.chatBox.scrollTop = elements.chatBox.scrollHeight;
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

    function addMessage(text, sender) {
        const messageDiv = document.createElement("div");
        messageDiv.className = `message ${sender}-message`;
        messageDiv.textContent = sanitizeInput(text);
        elements.chatBox.appendChild(messageDiv);
        elements.chatBox.scrollTop = elements.chatBox.scrollHeight;
        return messageDiv;
    }
}

// 初始化图片上传模块
function initImageUploadModule() {
    const elements = {
        imageUpload: getElementOrThrow("imageUpload"),
        uploadPreview: getElementOrThrow("uploadPreview"),
        resultContainer: getElementOrThrow("resultContainer"),
        processingOverlay: getElementOrThrow("processing"),
        detectedObjectsList: getElementOrThrow("detectedObjects"),
        wikiInfoContainer: getElementOrThrow("wikiInfoContainer")
    };

    elements.imageUpload.addEventListener("change", handleImageSelection);

    async function handleImageSelection(event) {
        const file = event.target.files[0];
        if (!file) return;

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

            displayDetectionResults(response);
            await displayProcessedImage(response.id);
        } catch (error) {
            console.error("图片处理失败:", error);
            alert(`图片处理失败: ${error.message}`);
        } finally {
            elements.processingOverlay.style.display = "none";
        }
    }

    function displayDetectionResults(response) {
        const detectedObjectsList = getElementOrThrow("detectedObjects");
        detectedObjectsList.innerHTML = "";

        if (response.labels && response.labels.length > 0) {
            detectedObjectsList.innerHTML = response.labels
                .map(label => `<li>${label}</li>`)
                .join("");

            if (response.wiki_info) {
                const wikiInfo = response.wiki_info;
                elements.wikiInfoContainer.innerHTML = `
                    <h3>关于 ${wikiInfo.title || '鸟类'}</h3>
                    <p>${wikiInfo.summary || "暂无介绍"}</p>
                    ${wikiInfo.image ? `<img src="${wikiInfo.image}" alt="鸟类图片" style="max-width:200px;">` : ""}
                    <p><a href="${wikiInfo.wiki_url}" target="_blank">查看更多</a></p>
                `;
            } else {
                elements.wikiInfoContainer.innerHTML = "<p>未找到相关 Wikipedia 介绍。</p>";
            }
        } else {
            detectedObjectsList.innerHTML = "<li>未检测到对象</li>";
            elements.wikiInfoContainer.innerHTML = "";
        }
    }

    async function displayProcessedImage(imageId) {
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
        "../images/01.jpg",
        "../images/02.jpg",
        "../images/03.jpg",
        "../images/04.png",
        "../images/05.png",
        "../images/06.png"
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

function sanitizeInput(text) {
    return text.toString().replace(/</g, "&lt;").replace(/>/g, "&gt;");
}