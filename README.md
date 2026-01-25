# Live Caption with Whisper App

This is the repo for a single-page Web app that displays live captions by using an OpenAI Whisper model.

## Getting Started - Auto Installation (Recommended for Windows & Linux users)

Depending on your system, you can find automatic installation scripts under the root folder.

**Windows:** `install_windows.ps1` (Open Terminal app, `cd` to where you download the code, run `.\install_windows.ps1`)    

**Linux:** `install_linux.sh` (Inside terminal, `cd` to where you download the code, run `sudo bash install_linux.sh`)    

**For Mac user:** There is an installation script under development: `install_mac.sh` (If you see an Rosetta warning, run exactly the following: `arch -arm64 zsh -lc './install_mac.sh'`). You can try running it but there is high chance of installation failure due to hardware/architecture compatibility issues on Mac. We recommend that Mac users use the [Manual Configuration](#getting-started---manual-configuration) below.     

## Getting Started - Manual Configuration 

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

> Additional note for Mac users: When running the last command, you may hit an error 
> saying `cmake` is not found. In such case please run `brew install cmake` 
> first, then re-run the last command.

**Activate the environment:**
- Mac & Linux: `source .venv/bin/activate`
- Windows: `.venv\Scripts\activate`

### Step 3 - Install whisper and other necessary dependencies

```bash
uv sync --python .venv
```

The command-line tool `ffmpeg` should also be installed on your system. 

**Windows / Mac:**   
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
