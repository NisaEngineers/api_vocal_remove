from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
import subprocess
import shutil
import uuid

app = FastAPI(title="Spleeter Audio Splitter API")

# Allow CORS (optional for public frontend access)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create temp and output folders
os.makedirs("uploads", exist_ok=True)
os.makedirs("separated", exist_ok=True)

@app.post("/separate/")
async def separate_audio(file: UploadFile = File(...)):
    if not file.filename.endswith((".mp3", ".wav", ".flac", ".m4a", ".ogg")):
        raise HTTPException(status_code=400, detail="Invalid audio format")

    # Save uploaded file
    unique_id = str(uuid.uuid4())
    input_path = f"uploads/{unique_id}_{file.filename}"
    with open(input_path, "wb") as f:
        content = await file.read()
        f.write(content)

    # Run spleeter
    output_dir = f"separated/{unique_id}"
    try:
        subprocess.run([
            "spleeter", "separate",
            "-p", "spleeter:2stems",
            "-o", output_dir,
            input_path
        ], check=True)
    except subprocess.CalledProcessError:
        raise HTTPException(status_code=500, detail="Spleeter failed to process the file")

    # Locate results
    base_name = os.path.splitext(os.path.basename(input_path))[0]
    stem_path = os.path.join(output_dir, base_name)
    vocals = os.path.join(stem_path, "vocals.wav")
    accompaniment = os.path.join(stem_path, "accompaniment.wav")

    if not os.path.exists(vocals) or not os.path.exists(accompaniment):
        raise HTTPException(status_code=500, detail="Spleeter output not found")

    return {
        "vocals_url": f"/download?v={unique_id}&type=vocals",
        "accompaniment_url": f"/download?v={unique_id}&type=accompaniment"
    }

@app.get("/download")
def download_file(v: str, type: str):
    folder = f"separated/{v}"
    if type not in ["vocals", "accompaniment"]:
        raise HTTPException(status_code=400, detail="Invalid type")

    # Find subfolder with actual file
    for sub in os.listdir(folder):
        path = os.path.join(folder, sub, f"{type}.wav")
        if os.path.exists(path):
            return FileResponse(path, media_type="audio/wav", filename=f"{type}.wav")

    raise HTTPException(status_code=404, detail="File not found")

