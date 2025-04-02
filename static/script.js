document.addEventListener("DOMContentLoaded", () => {
    try {
        initChatModule();
        initImageUploadModule();
    } catch (error) {
        console.error("初始化失败:", error);
        alert("系统初始化失败，请刷新页面");
    }
});
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
    // 获取元素
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

    // 获取发送按钮的图标
    const sendIcon = document.getElementById("sendIcon");

    // 设置图标为“思考中”状态
    sendIcon.innerHTML = '⏳';  // 替换为旋转图标或其他占位符
    sendIcon.classList.add('thinking-icon');  // 添加旋转动画

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
        // 回复后恢复原图标
        sendIcon.innerHTML = '🚀';  // 恢复箭头图标
        sendIcon.classList.remove('thinking-icon');  // 移除旋转动画
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
        resultContainer: getElementOrThrow("resultContainer"), // 添加结果展示区域
        processingOverlay: getElementOrThrow("processing"),
        detectedObjectsList: getElementOrThrow("detectedObjects") // 检测结果列表
    };

    // 监听文件选择
    elements.imageUpload.addEventListener("change", handleImageSelection);

    async function handleImageSelection(event) {
        const file = event.target.files[0];
        if (!file) return;

        // 显示加载状态
        elements.processingOverlay.style.display = "grid";
        elements.detectedObjectsList.innerHTML = ""; // 清空之前的检测结果

        try {
            // 1. 显示预览
            const objectUrl = URL.createObjectURL(file);
            elements.uploadPreview.style.backgroundImage = `url(${objectUrl})`;
            elements.uploadPreview.onload = () => URL.revokeObjectURL(objectUrl);

            // 2. 上传图片到后端进行识别
            const formData = new FormData();
            formData.append("file", file);

            const response = await safeFetch("http://127.0.0.1:8000/yolo/upload", {
                method: "POST",
                body: formData // 不需要设置 Content-Type，浏览器会自动处理
            });

            // 3. 显示检测结果
            displayDetectionResults(response);

            // 4. 获取并显示处理后的图片
            await displayProcessedImage(response.id);

        } catch (error) {
            console.error("图片处理失败:", error);
            alert(`图片处理失败: ${error.message}`);
        } finally {
            elements.processingOverlay.style.display = "none";
        }
    }

    function displayDetectionResults(response) {
        // 显示检测到的对象列表
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
            // 获取处理后的图片
            const imageResponse = await fetch(`http://127.0.0.1:8000/yolo/download/${imageId}`);

            if (!imageResponse.ok) {
                throw new Error(`获取处理后的图片失败: ${imageResponse.status}`);
            }

            // 将图片转换为 Blob URL
            const imageBlob = await imageResponse.blob();
            const processedImageUrl = URL.createObjectURL(imageBlob);

            // 创建并显示处理后的图片
            const processedImg = document.createElement("img");
            processedImg.src = processedImageUrl;
            processedImg.alt = "处理后的图片";
            processedImg.style.maxWidth = "100%";

            // 清空并更新结果容器
            elements.resultContainer.innerHTML = "";
            elements.resultContainer.appendChild(processedImg);

            // 释放 URL 防止内存泄漏
            processedImg.onload = () => URL.revokeObjectURL(processedImageUrl);

        } catch (error) {
            console.error("显示处理图片失败:", error);
            elements.resultContainer.innerHTML = "<p>无法显示处理后的图片</p>";
        }
    }
}
// 通用工具函数
function getElementOrThrow(id) {
    const element = document.getElementById(id);
    if (!element) throw new Error(`未找到元素: ${id}`);
    return element;
}

function sanitizeInput(text) {
    return text.toString().replace(/</g, "&lt;").replace(/>/g, "&gt;");
}