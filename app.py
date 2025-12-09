from fastapi import FastAPI, File, UploadFile, BackgroundTasks, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
import shutil, os, subprocess, json
from pathlib import Path

app = FastAPI()
BASE_DIR = Path(__file__).parent

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/ingest/")
async def ingest(file: UploadFile = File(...)):
    dst = BASE_DIR / file.filename
    with open(dst, "wb") as f:
        shutil.copyfileobj(file.file, f)
    # In production: push to cloud storage, emit a job to queue.
    return {"status":"uploaded","filename":file.filename}

@app.post("/process/")
async def process(filename: str = Form(...), background: BackgroundTasks = BackgroundTasks()):
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

@app.get("/transcript/")
def get_transcript():
    """Retrieve the generated transcript."""
    transcript_path = BASE_DIR / "transcript.json"
    if not transcript_path.exists():
        raise HTTPException(status_code=404, detail="Transcript not found. Please process a file first.")
    with open(transcript_path, "r") as f:
        transcript = json.load(f)
    return {"transcript": transcript}

@app.get("/tasks/")
def get_tasks():
    """Retrieve the extracted tasks."""
    tasks_path = BASE_DIR / "tasks.json"
    if not tasks_path.exists():
        raise HTTPException(status_code=404, detail="Tasks not found. Please process a file first.")
    with open(tasks_path, "r") as f:
        tasks = json.load(f)
    return {"tasks": tasks}
