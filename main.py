import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import numpy as np
import io
import audioop
import wave
import whisper
import torch
from typing import Optional

# Initialize FastAPI application
app = FastAPI()

# Load the Whisper model (important: choose a lightweight model for realtime use)
# Optional models: tiny < base < small < medium < large (speed ↓, accuracy ↑)
# Recommended to try "base" first for a balance of speed and accuracy
model = whisper.load_model(
    "base.en",  # model name, possible options: tiny, base, small, medium, large, turbo (tiny.en, base.en, small.en, medium.en for models tuned for English)
    device= "cuda" if torch.cuda.is_available() else "cpu",  # auto-detect GPU/CPU
    in_memory=True  # keep model in memory to reduce latency
)

# Audio configuration (ensure frontend and backend match)
AUDIO_SAMPLE_RATE = 16000  # sample rate required by Whisper
AUDIO_CHANNELS = 1  # mono
AUDIO_SAMPLE_WIDTH = 2  # 16-bit depth

# Mount static files (for serving the frontend page)
app.mount("/static", StaticFiles(directory="./static"), name="static")

# Store active WebSocket connections
active_connections: list[WebSocket] = []

@app.get("/")
async def get_frontend():
    """Return the frontend page"""
    return FileResponse("./static/index.html")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    audio_frames = []  # buffer audio frames for concatenation
    try:
        while True:
            # Receive audio binary data sent from the frontend
            data = await websocket.receive_bytes()
            if not data:
                continue
            
            # Process audio: convert to Whisper's required format (16kHz, mono, float32)
            # Step 1: convert PCM audio (16-bit) to float32
            audio_np = np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.0
            # Step 2: ensure sample rate is 16kHz (resample if frontend differs; simplified here)
            audio_frames.append(audio_np)
            
            # Transcribe every 3 seconds of audio (16kHz*3=48000 frames) to balance latency and accuracy
            total_frames = sum(len(frame) for frame in audio_frames)
            if total_frames >= AUDIO_SAMPLE_RATE * 3:
                full_audio = np.concatenate(audio_frames)
                audio_frames = []  # 清空缓存
                
                # Perform transcription (use Whisper's transcribe with real-time-oriented parameters)
                result = model.transcribe(
                    full_audio,
                    language="en",  # specify language ("zh" for Chinese, "en" for English, leave empty for auto)
                    fp16=torch.cuda.is_available(),  # enable FP16 on GPU for acceleration
                    verbose=False,  # disable verbose logging
                    no_speech_threshold=0.1,  # lower no-speech threshold
                    condition_on_previous_text=False  # do not condition on previous text (favor realtime)
                )
                
                # Send transcription result back to the frontend
                transcription = result["text"].strip()
                if transcription:
                    await websocket.send_text(transcription)
    
    except WebSocketDisconnect:
        active_connections.remove(websocket)
    except Exception as e:
        print(f"Error: {e}")
        await websocket.send_text(f"[Error] {str(e)}")
       
if __name__ == "__main__":
    # Run FastAPI server (host=0.0.0.0 allows LAN access)
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True  # watch for file changes and reload the server
    )
