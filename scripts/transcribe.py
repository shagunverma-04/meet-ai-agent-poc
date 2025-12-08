# Minimal transcription script.
# Supports local Whisper if installed, else falls back to a dummy placeholder.
import argparse, json, os, sys
from tqdm import tqdm

def whisper_transcribe(audio_path, model_name="small"):
    try:
        import whisper
    except Exception as e:
        print("Whisper not installed. Install with: pip install -U openai-whisper")
        raise
    model = whisper.load_model(model_name)
    print("Transcribing with whisper model:", model_name)
    result = model.transcribe(audio_path, language='en')
    # result contains 'segments' with start, end, text
    transcript = []
    for seg in result.get("segments", []):
        transcript.append({"start": seg["start"], "end": seg["end"], "text": seg["text"]})
    return transcript

def save_transcript(transcript, out="transcript.json"):
    with open(out, "w") as f:
        json.dump(transcript, f, indent=2)
    print("Saved transcript to", out)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("audio", help="audio file path")
    parser.add_argument("--model", default="small", help="whisper model name")
    args = parser.parse_args()
    try:
        transcript = whisper_transcribe(args.audio, args.model)
    except Exception as e:
        # Fallback: create a dummy transcript to demonstrate downstream flow
        print("Falling back to dummy transcript due to:", e)
        transcript = [
            {"start": 0.0, "end": 5.0, "text":"We need to create onboarding mockups by next Monday."},
            {"start": 5.1, "end": 9.0, "text":"Sanya will take that."},
            {"start": 9.1, "end": 15.0, "text":"Also, backend should add analytics events."}
        ]
    save_transcript(transcript, out="transcript.json")
