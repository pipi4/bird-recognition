document.addEventListener("DOMContentLoaded", () => {
    try {
        initChatModule();
        initImageUploadModule();
        initBirdFactModule();  // 初始化鸟类趣闻模块
    } catch (error) {
        console.error("初始化失败:", error);
        alert("系统初始化失败，请刷新页面");
    }
});

// 通用工具函数
function getElementOrThrow(id) {
    const element = document.getElementById(id);
    if (!element) throw new Error(`未找到元素: ${id}`);
    return element;
}

async function safeFetch(url, options) {
    try {
        // 发起请求
        const response = await fetch(url, options);

        // 如果响应不成功，则抛出错误
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }

        // 返回响应体的 JSON 数据
        return await response.json();
    } catch (error) {
        // 捕获错误并输出
        console.error("请求出错:", error);
        throw error; // 重新抛出错误
    }
}

function initChatModule() {
    const elements = {
        chatBox: getElementOrThrow("chatBox"),
        inputField: getElementOrThrow("question"),
        sendButton: getElementOrThrow("sendBtn")
    };

    // 事件监听
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
        sendIcon.innerHTML = '⏳';
        sendIcon.classList.add('thinking-icon');

        const loadingMsg = addMessage("🤖 思考中...", "bot");

        try {
            const data = await safeFetch("http://127.0.0.1:8000/deepseek/ask", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ question })
            });

            loadingMsg.textContent = data.answer || "未找到相关信息";
        } catch (error) {
            loadingMsg.textContent = `错误: ${error.message}`;
            console.error("消息发送失败:", error);
        } finally {
            sendIcon.innerHTML = '🚀';
            sendIcon.classList.remove('thinking-icon');
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

function initImageUploadModule() {
    const elements = {
        imageUpload: getElementOrThrow("imageUpload"),
        uploadPreview: getElementOrThrow("uploadPreview"),
        resultContainer: getElementOrThrow("resultContainer"),
        processingOverlay: getElementOrThrow("processing"),
        detectedObjectsList: getElementOrThrow("detectedObjects")
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

            const response = await safeFetch("http://127.0.0.1:8000/yolo/upload", {
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
        if (response.labels && response.labels.length > 0) {
            elements.detectedObjectsList.innerHTML = response.labels
                .map(label => `<li>${label}</li>`)
                .join("");
        } else {
            elements.detectedObjectsList.innerHTML = "<li>未检测到对象</li>";
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

function initBirdFactModule() {
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

    const factBox = document.getElementById("factBox");
    const factContainer = document.querySelector(".fact-container");

    function updateFact() {
        factBox.innerText = facts[Math.floor(Math.random() * facts.length)];
    }

    updateFact();
    let factInterval = setInterval(updateFact, 30000);

    const birdImages = [
        "../images/01.jpg",
        "../images/02.jpg",
        "../images/03.jpg",
        "../images/04.png",
        "../images/05.png",
        "../images/06.png"
    ];

    function changeBackground() {
        const randomImage = birdImages[Math.floor(Math.random() * birdImages.length)];
        factContainer.style.backgroundImage = `url(${randomImage})`;
    }

    changeBackground();
    let backgroundInterval = setInterval(changeBackground, 30000);

    document.getElementById("themeToggle").addEventListener("click", () => {
        document.body.classList.toggle("dark-mode");
        const currentTheme = document.body.classList.contains("dark-mode") ? "dark" : "light";
        document.documentElement.setAttribute("data-theme", currentTheme);

        if (currentTheme === "dark") {
            updateFact();
            changeBackground();
        }
    });
}

function sanitizeInput(text) {
    return text.toString().replace(/</g, "&lt;").replace(/>/g, "&gt;");
}
