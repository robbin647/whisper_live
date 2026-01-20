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
from collections import deque

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

class _AudioRing:
    def __init__(self, max_samples: int):
        self._frames: deque[np.ndarray] = deque()
        self._total_samples = 0
        self._max_samples = max_samples

    @property
    def total_samples(self) -> int:
        return self._total_samples

    def append(self, audio: np.ndarray) -> None:
        if audio.size == 0:
            return
        self._frames.append(audio)
        self._total_samples += int(audio.size)

        while self._total_samples > self._max_samples and self._frames:
            extra = self._total_samples - self._max_samples
            head = self._frames[0]
            if head.size <= extra:
                self._frames.popleft()
                self._total_samples -= int(head.size)
            else:
                self._frames[0] = head[extra:]
                self._total_samples -= int(extra)

    def last(self, n_samples: int) -> np.ndarray:
        if n_samples <= 0 or self._total_samples == 0:
            return np.zeros(0, dtype=np.float32)

        if n_samples >= self._total_samples:
            return np.concatenate(list(self._frames), axis=0) if self._frames else np.zeros(0, dtype=np.float32)

        remaining = n_samples
        parts: list[np.ndarray] = []
        for arr in reversed(self._frames):
            if remaining <= 0:
                break
            if arr.size <= remaining:
                parts.append(arr)
                remaining -= int(arr.size)
            else:
                parts.append(arr[-remaining:])
                remaining = 0

        if not parts:
            return np.zeros(0, dtype=np.float32)
        return np.concatenate(list(reversed(parts)), axis=0)

class _SlidingWindowWhisper:
    def __init__(
        self,
        model: whisper.Whisper,
        sample_rate: int,
        *,
        window_seconds: float = 5.0,
        step_seconds: float = 1.0,
        commit_lag_seconds: float = 1.0,
        max_seconds: float = 8.0,
        silence_flush_seconds: float = 1.2,
        speech_rms_threshold: float = 0.008,
        prompt_chars: int = 200,
        language: str = "en",
    ):
        self._model = model
        self._sr = int(sample_rate)
        self._window_samples = max(1, int(window_seconds * self._sr))
        self._step_samples = max(1, int(step_seconds * self._sr))
        self._commit_lag_seconds = float(commit_lag_seconds)
        self._silence_flush_samples = max(1, int(silence_flush_seconds * self._sr))
        self._speech_rms_threshold = float(speech_rms_threshold)
        self._prompt_chars = int(prompt_chars)
        self._language = language

        self._ring = _AudioRing(max_samples=max(1, int(max_seconds * self._sr)))
        self._stream_samples = 0
        self._samples_since_decode = 0
        self._silent_samples = 0

        self._last_committed_time = 0.0
        self._transcript = ""

    @property
    def transcript(self) -> str:
        return self._transcript

    def push(self, audio: np.ndarray) -> None:
        if audio.size == 0:
            return
        rms = float(np.sqrt(np.mean(np.square(audio))))
        if rms >= self._speech_rms_threshold:
            self._silent_samples = 0
        else:
            self._silent_samples += int(audio.size)

        self._ring.append(audio)
        self._stream_samples += int(audio.size)
        self._samples_since_decode += int(audio.size)

    def maybe_transcribe(self) -> str:
        if self._ring.total_samples < int(1.0 * self._sr):
            return ""

        force_flush = self._silent_samples >= self._silence_flush_samples
        if not force_flush and self._samples_since_decode < self._step_samples:
            return ""

        total_time = self._stream_samples / self._sr
        window_audio = self._ring.last(self._window_samples)
        window_audio = window_audio - float(np.mean(window_audio)) if window_audio.size else window_audio
        window_start = total_time - (window_audio.size / self._sr)

        prompt = self._transcript[-self._prompt_chars :].strip()

        result = self._model.transcribe(
            window_audio,
            language=self._language,
            fp16=torch.cuda.is_available(),
            verbose=False,
            temperature=0,
            beam_size=5,
            condition_on_previous_text=False,
            initial_prompt=prompt if prompt else None,
            no_speech_threshold=0.6,
            logprob_threshold=-1.0,
            compression_ratio_threshold=2.4,
        )

        segments = result.get("segments") or []
        commit_lag = 0.0 if force_flush else self._commit_lag_seconds
        commit_cutoff = total_time - commit_lag

        committed_text_parts: list[str] = []
        max_committed_end = self._last_committed_time

        for seg in segments:
            seg_text = (seg.get("text") or "").strip()
            if not seg_text:
                continue

            abs_end = window_start + float(seg.get("end", 0.0))
            if abs_end <= commit_cutoff and abs_end > self._last_committed_time + 1e-3:
                committed_text_parts.append(seg_text)
                if abs_end > max_committed_end:
                    max_committed_end = abs_end

        self._samples_since_decode = 0

        if not committed_text_parts:
            return ""

        new_commit = " ".join(committed_text_parts).strip()
        delta = self._dedupe_delta(self._transcript, new_commit)

        if delta:
            self._transcript = (self._transcript + " " + delta).strip() if self._transcript else delta
        self._last_committed_time = max_committed_end

        return delta

    def _dedupe_delta(self, existing: str, addition: str) -> str:
        addition_words = addition.split()
        if not addition_words:
            return ""
        if not existing:
            return addition

        tail_words = existing.split()[-60:]
        max_k = min(len(tail_words), len(addition_words))
        best_k = 0
        for k in range(1, max_k + 1):
            if tail_words[-k:] == addition_words[:k]:
                best_k = k
        return " ".join(addition_words[best_k:]).strip()

@app.get("/")
async def get_frontend():
    """Return the frontend page"""
    return FileResponse("./static/index.html")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)

    transcriber = _SlidingWindowWhisper(model, AUDIO_SAMPLE_RATE)

    try:
        while True:
            data = await websocket.receive_bytes()
            if not data:
                continue

            audio_np = np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.0
            transcriber.push(audio_np)

            delta = transcriber.maybe_transcribe()
            if delta:
                await websocket.send_text(delta)

    except WebSocketDisconnect:
        if websocket in active_connections:
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