import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import numpy as np
import io
import audioop
import wave
import whisper
from typing import Optional

# 初始化FastAPI应用
app = FastAPI()

# 加载Whisper模型（关键：选轻量模型保证实时性）
# 可选模型：tiny < base < small < medium < large（速度↓，准确率↑）
# 建议先试用base，兼顾速度和准确率
model = whisper.load_model(
    "base.en",  # 模型名称
    device= "cpu",  # 自动检测GPU/CPU
    in_memory=True  # 模型加载到内存，减少延迟
)

# 音频配置（保证前后端一致）
AUDIO_SAMPLE_RATE = 16000  # Whisper要求的采样率
AUDIO_CHANNELS = 1  # 单声道
AUDIO_SAMPLE_WIDTH = 2  # 16位深度

# 挂载静态文件（用于访问前端页面）
app.mount("/static", StaticFiles(directory="./static"), name="static")

# 存储活跃的WebSocket连接
active_connections: list[WebSocket] = []

@app.get("/")
async def get_frontend():
    """返回前端页面"""
    return FileResponse("./static/index.html")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    audio_frames = []  # 缓存音频帧，用于拼接分块
    try:
        while True:
            # 接收前端发送的音频二进制数据
            data = await websocket.receive_bytes()
            if not data:
                continue
            
            # 处理音频：转换为Whisper要求的格式（16kHz、单声道、float32）
            # 步骤1：将PCM音频（16位）转换为float32
            audio_np = np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.0
            # 步骤2：确保采样率为16kHz（如果前端采样率不同，需重采样，这里简化）
            audio_frames.append(audio_np)
            
            # 每收集3秒音频（16kHz*3=48000帧），执行一次转录（平衡延迟和准确率）
            total_frames = sum(len(frame) for frame in audio_frames)
            if total_frames >= AUDIO_SAMPLE_RATE * 3:
                full_audio = np.concatenate(audio_frames)
                audio_frames = []  # 清空缓存
                
                # 执行转录（使用Whisper的transcribe，设置实时参数）
                result = model.transcribe(
                    full_audio,
                    language="zh",  # 指定语言（中文填zh，英文填en，自动检测留空）
                    fp16=False,  # GPU启用FP16加速
                    verbose=False,  # 关闭详细日志
                    no_speech_threshold=0.1,  # 降低无语音阈值
                    condition_on_previous_text=False  # 不依赖前文（实时性优先）
                )
                
                # 将转录结果发送回前端
                transcription = result["text"].strip()
                if transcription:
                    await websocket.send_text(transcription)
    
    except WebSocketDisconnect:
        active_connections.remove(websocket)
    except Exception as e:
        print(f"错误：{e}")
        await websocket.send_text(f"[错误] {str(e)}")
       
if __name__ == "__main__":
    # 启动FastAPI服务（host=0.0.0.0允许局域网访问）
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True  # 开发模式，修改代码自动重启
    )
