let fromSampleRate = 16000;
let toSampleRate = 22050;

self.onmessage = function(e) {
    const { type, data } = e.data;
    
    if (type === 'init') {
        fromSampleRate = data.fromSampleRate;
        toSampleRate = data.toSampleRate;
    } else if (type === 'process') {
        const audioData = data;
        const pcmData = new Float32Array(audioData);
        
        // 重采样
        const ratio = fromSampleRate / toSampleRate;
        const newLength = Math.round(pcmData.length / ratio);
        const result = new Float32Array(newLength);
        
        for (let i = 0; i < newLength; i++) {
            const position = i * ratio;
            const left = Math.floor(position);
            const right = left + 1;
            const fraction = position - left;
            
            if (right >= pcmData.length) {
                result[i] = pcmData[left];
            } else {
                result[i] = pcmData[left] * (1 - fraction) + pcmData[right] * fraction;
            }
        }
        
        self.postMessage({
            audioData: result,
            pcmAudioData: pcmData
        });
    }
}; 