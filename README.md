# Live Caption with Whisper App

This is the repo for a single-page Web app that displays live captions by using an OpenAI Whisper model.

## Getting Started

### Step 1 - Install uv package manager

**Windows:**
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**Mac / Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Step 2 - Create and activate a virtual environment

```bash
cd /path/to/your/downloaded/code
uv init && uv venv
```

**Activate the environment:**
- Mac & Linux: `source .venv/bin/activate`
- Windows: `.venv\Scripts\activate`

### Step 3 - Install whisper and other necessary dependencies

```bash
uv pip install -r requirements.txt
```

The command-line tool ffmpeg should also be installed on your system. Please visit their website: [https://ffmpeg.org/download.html](https://ffmpeg.org/download.html)

If prompted, you may need to install librosa:

```bash
uv add librosa
```

### Step 4 - Run FastAPI server

```bash
uv run main.py
```

### Step 5 - Access http://localhost:8000

Open your web browser and navigate to [http://localhost:8000](http://localhost:8000)

## References

1. [OpenAI Whisper GitHub](https://github.com/openai/whisper)
2. [Whisper LibriSpeech Notebook](https://colab.research.google.com/github/openai/whisper/blob/master/notebooks/LibriSpeech.ipynb)