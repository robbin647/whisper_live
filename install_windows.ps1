Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $scriptDir

if (-not (Test-Path "pyproject.toml")) {
    Write-Error "Run this script from the repo root (missing pyproject.toml)."
}

if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Host "Installing uv..."
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
}

$localBin = Join-Path $env:USERPROFILE ".local\bin"
if (Test-Path $localBin) {
    if ($env:Path -notlike "*$localBin*") {
        $env:Path = "$localBin;$env:Path"
    }
}

Write-Host "Installing Python 3.12 via uv..."
uv python install 3.12

if (-not (Test-Path ".venv")) {
    Write-Host "Creating virtual environment..."
    uv venv
}

Write-Host "Installing Python dependencies..."
uv pip install -r requirements.txt --python .venv

if (-not (Get-Command ffmpeg -ErrorAction SilentlyContinue)) {
    Write-Host ""
    Write-Host "Installing ffmpeg..."
    
    $ffmpegUrl = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
    $tempZip = Join-Path $env:TEMP "ffmpeg-8.0.1-essentials_build.zip"
    $ffmpegDir = Join-Path $env:USERPROFILE ".local\ffmpeg"
    
    # Download ffmpeg
    Write-Host "Downloading ffmpeg from $ffmpegUrl..."
    Invoke-WebRequest -Uri $ffmpegUrl -OutFile $tempZip
    
    # Extract to temporary location
    $tempExtract = Join-Path $env:TEMP "ffmpeg_extract"
    if (Test-Path $tempExtract) {
        Remove-Item $tempExtract -Recurse -Force
    }
    Write-Host "Extracting ffmpeg..."
    Expand-Archive -Path $tempZip -DestinationPath $tempExtract -Force
    
    # Move contents, stripping top-level folder
    $topLevelFolder = Get-ChildItem $tempExtract | Select-Object -First 1
    if (Test-Path $ffmpegDir) {
        Remove-Item $ffmpegDir -Recurse -Force
        mkdir $ffmpegDir
    }
    New-Item -ItemType Directory -Path $ffmpegDir -Force | Out-Null
    
    # Move the contents of the top-level folder, not the folder itself
    Get-ChildItem -Path $topLevelFolder.FullName | Move-Item -Destination $ffmpegDir
    
    # Clean up
    Remove-Item $tempZip -Force
    Remove-Item $tempExtract -Recurse -Force
    
    # Add to PATH for current session
    $ffmpegBin = Join-Path $ffmpegDir "bin"
    if ($env:Path -notlike "*$ffmpegBin*") {
        $env:Path = "$ffmpegBin;$env:Path"
    }
    
    # Add to user PATH permanently
    $userPath = [Environment]::GetEnvironmentVariable("Path", "User")
    if ($userPath -notlike "*$ffmpegBin*") {
        [Environment]::SetEnvironmentVariable("Path", "$ffmpegBin;$userPath", "User")
        Write-Host "Added ffmpeg to user PATH."
    }
    
    Write-Host "ffmpeg installed successfully!"
}

Write-Host ""
Write-Host "To start, run the following command:"
Write-Host "  uv run main.py"
