/**
 * Camera Live Detection Handler
 * Handles opening camera and performing real-time object detection
 */
document.addEventListener('DOMContentLoaded', () => {
    const cameraBtn = document.getElementById('cameraBtn');
    if (cameraBtn) {
        cameraBtn.addEventListener('click', toggleCamera);
    }
});

// Global variables
let stream = null;
let isStreaming = false;
let videoElement = null;
let detectionInterval = null;
let processingImage = false;

/**
 * Toggle camera state (on/off)
 */
async function toggleCamera() {
    if (!isStreaming) {
        await startCamera();
    } else {
        stopCamera();
    }
}

/**
 * Start camera stream and detection
 */
async function startCamera() {
    try {
        // Get preview container
        const previewContainer = document.getElementById('uploadPreview');
        const cameraBtn = document.getElementById('cameraBtn');
        
        if (!previewContainer) {
            throw new Error('Preview container not found');
        }

        // Create video element
        videoElement = document.createElement('video');
        videoElement.setAttribute('autoplay', '');
        videoElement.setAttribute('playsinline', ''); // For iOS support
        videoElement.style.width = '100%';
        videoElement.style.height = '100%';
        videoElement.style.objectFit = 'contain';

        // Request camera access
        stream = await navigator.mediaDevices.getUserMedia({
            video: {
                facingMode: 'environment', // Use back camera when available
                width: { ideal: 1280 },
                height: { ideal: 720 }
            }
        });

        // Setup video stream
        videoElement.srcObject = stream;
        previewContainer.innerHTML = '';
        previewContainer.appendChild(videoElement);

        // Show processing overlay
        const processingOverlay = document.getElementById('processing');
        if (processingOverlay) {
            processingOverlay.style.display = 'flex';
        }

        // Update button
        if (cameraBtn) {
            cameraBtn.textContent = '📹 关闭相机';
            cameraBtn.classList.add('active');
        }

        isStreaming = true;

        // Start detection after video is loaded
        videoElement.onloadedmetadata = () => {
            startDetectionLoop();
            if (processingOverlay) {
                processingOverlay.style.display = 'none';
            }
        };

    } catch (error) {
        console.error('Camera error:', error);
        alert('无法访问摄像头: ' + error.message);
        stopCamera();
    }
}

/**
 * Stop camera stream and detection
 */
function stopCamera() {
    // Stop detection interval
    if (detectionInterval) {
        clearInterval(detectionInterval);
        detectionInterval = null;
    }

    // Stop camera stream
    if (stream) {
        stream.getTracks().forEach(track => track.stop());
        stream = null;
    }

    // Remove video element
    if (videoElement) {
        videoElement.remove();
        videoElement = null;
    }

    // Reset UI
    const previewContainer = document.getElementById('uploadPreview');
    if (previewContainer) {
        previewContainer.innerHTML = '<div class="placeholder-text">请上传图片或视频进行识别</div>';
    }

    const cameraBtn = document.getElementById('cameraBtn');
    if (cameraBtn) {
        cameraBtn.textContent = '📹 打开相机';
        cameraBtn.classList.remove('active');
    }

    const processingOverlay = document.getElementById('processing');
    if (processingOverlay) {
        processingOverlay.style.display = 'none';
    }

    isStreaming = false;
}

/**
 * Start continuous detection loop
 */
function startDetectionLoop() {
    const canvas = document.createElement('canvas');
    const context = canvas.getContext('2d');

    detectionInterval = setInterval(async () => {
        if (!isStreaming || !videoElement || processingImage) {
            return;
        }

        try {
            processingImage = true;
            
            // Set canvas dimensions to match video
            canvas.width = videoElement.videoWidth;
            canvas.height = videoElement.videoHeight;

            // Capture frame
            context.drawImage(videoElement, 0, 0);

            // Convert to blob
            const blob = await new Promise(resolve => {
                canvas.toBlob(resolve, 'image/jpeg', 0.8);
            });

            // Send to server for detection
            const formData = new FormData();
            formData.append('file', blob, 'camera_frame.jpg');

            const response = await fetch('/yolo/upload', {
                method: 'POST',
                body: formData
            });

            if (response.ok) {
                const result = await response.json();
                updateResults(result);
            }
        } catch (error) {
            console.error('Detection error:', error);
        } finally {
            processingImage = false;
        }
    }, 1000); // Process one frame per second
}

/**
 * Update detection results in the UI
 */
function updateResults(result) {
    // Update detected objects list
    const detectedObjectsList = document.getElementById('detectedObjects');
    if (detectedObjectsList) {
        if (result.labels && Object.keys(result.labels).length > 0) {
            const objectsHtml = Object.keys(result.labels).map(label => {
                return `<li class="detected-item">
                    <span class="object-name">${label}</span>
                </li>`;
            }).join('');
            detectedObjectsList.innerHTML = objectsHtml;
        } else {
            detectedObjectsList.innerHTML = '<li class="no-detection">未检测到物体</li>';
        }
    }

    // Update result image
    const resultContainer = document.getElementById('resultContainer');
    if (resultContainer && result.id) {
        resultContainer.innerHTML = `
            <img src="/yolo/download/${result.id}" 
                alt="Detection result" 
                style="max-width: 100%; height: auto;">`;
    }

    // Update wiki info
    if (result.wiki_info) {
        const wikiInfoContainer = document.getElementById('wikiInfoContainer');
        if (wikiInfoContainer) {
            let wikiHtml = `<h3>${result.wiki_info.title}</h3>`;
            wikiHtml += `<p>${result.wiki_info.summary}</p>`;
            
            if (result.wiki_info.image) {
                wikiHtml += `<img src="${result.wiki_info.image}" alt="${result.wiki_info.title}" style="max-width: 100%; height: auto;">`;
            }
            
            if (result.wiki_info.wiki_url) {
                wikiHtml += `<p><a href="${result.wiki_info.wiki_url}" target="_blank">了解更多</a></p>`;
            }
            
            wikiInfoContainer.innerHTML = wikiHtml;
        }
    }
} 