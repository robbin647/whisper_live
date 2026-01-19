# Live Caption with Whisper App

This is the repo for a single-page Web app that displays live captions by using an OpenAI Whisper model.

## Getting Started

### Step 1 - Install uv package manager and Python

**Windows:**
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**Mac / Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Then, run the following command to have Python 3.12 installed.

```bash
uv python install 3.12
```

### Step 2 - Install python and activate a virtual environment

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

The command-line tool `ffmpeg` should also be installed on your system. 

**Windows / Mac **   
Visit official website: [https://ffmpeg.org/download.html](https://ffmpeg.org/download.html), you can find download link under the  "Get packages & executable files" section.


**Linux **

```bash
mkdir -p ~/.local/bin && \
wget https://github.com/ffbinaries/ffbinaries-prebuilt/releases/download/v6.1/ffmpeg-6.1-linux-64.zip && \
unzip -d ~/.local/bin ffmpeg-6.1-linux-64.zip && \
export PATH="$(realpath ~/.local/bin):$PATH"
```

### Step 4 - Start FastAPI server

```bash
uv run main.py
```

### Step 5 - Access http://localhost:8000

Open your web browser and navigate to [http://localhost:8000](http://localhost:8000)

## References

1. [OpenAI Whisper GitHub](https://github.com/openai/whisper)
2. [Whisper LibriSpeech Notebook](https://colab.research.google.com/github/openai/whisper/blob/master/notebooks/LibriSpeech.ipynb)