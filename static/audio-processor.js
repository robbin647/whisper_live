class AudioProcessor extends AudioWorkletProcessor {
    constructor() {
        super();
        this.buffer = [];
    }

    process(inputs, outputs, parameters) {
        const input = inputs[0];
        if (input && input[0]) {
            // 发送音频数据到主线程
            this.port.postMessage(input[0]);
        }
        return true;
    }
}

registerProcessor('audio-processor', AudioProcessor);
