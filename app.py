from fastapi import FastAPI, File, UploadFile, BackgroundTasks
import shutil, os, subprocess, json
from pathlib import Path

app = FastAPI()
BASE_DIR = Path(__file__).parent

@app.post("/ingest/")
async def ingest(file: UploadFile = File(...)):
    dst = BASE_DIR / file.filename
    with open(dst, "wb") as f:
        shutil.copyfileobj(file.file, f)
    # In production: push to cloud storage, emit a job to queue.
    return {"status":"uploaded","filename":file.filename}

@app.post("/process/")
async def process(filename: str, background: BackgroundTasks):
    # Spawn background task to run the pipeline synchronously in PoC
    filepath = BASE_DIR / filename
    if not filepath.exists():
        return {"error":"file not found"}
    audio_path = BASE_DIR / "audio.wav"
    # extract
    subprocess.run(["ffmpeg","-y","-i", str(filepath), "-vn","-acodec","pcm_s16le","-ar","16000","-ac","1", str(audio_path)], check=False)
    # transcribe (calls script)
    subprocess.run(["python","scripts/transcribe.py", str(audio_path)], check=False)
    # extract tasks
    subprocess.run(["python","scripts/extract_tasks.py","transcript.json","--meeting_date","2025-12-01"], check=False)
    return {"status":"processing_started"}

@app.get("/health")
def health():
    return {"status":"ok"}
