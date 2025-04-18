import os
import uuid
import threading
import subprocess
from fastapi import FastAPI, UploadFile, File, Form, Depends, Header, HTTPException, status, Request
from fastapi.responses import FileResponse

# In-memory job store
jobs = {}
jobs_lock = threading.Lock()


def process_video(job_id: str, fps: int):
    with jobs_lock:
        jobs[job_id]["status"] = "processing"
    try:
        input_path = jobs[job_id]["input_path"]
        output_path = jobs[job_id]["output_path"]
        palette_path = output_path + ".palette.gif"
        cmd = [
            "ffmpeg",
            "-i", input_path,
            "-vf", "fps=16,scale=iw:-1:flags=spline,palettegen",
            "-y", palette_path,
        ]
        subprocess.run(cmd, check=True)

        cmd = [
            "ffmpeg",
            "-i", input_path,
            "-i", palette_path,
            "-lavfi", "fps=16,scale=iw:-1:flags=spline [x]; [x][1:v] paletteuse=dither=bayer",
            "-y", output_path,
        ]
        subprocess.run(cmd, check=True)
        with jobs_lock:
            jobs[job_id]["status"] = "finished"
    except subprocess.CalledProcessError as e:
        with jobs_lock:
            jobs[job_id]["status"] = "failed"
            jobs[job_id]["error"] = str(e)
    finally:
        try:
            os.remove(input_path)
        except Exception:
            pass


async def get_api_key(x_api_key: str = Header(...)):
    api_key = os.getenv("API_KEY")
    if api_key is None:
        raise HTTPException(status_code=500, detail="API_KEY not configured")
    if x_api_key != api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API Key")
    return x_api_key

app = FastAPI()


@app.on_event("startup")
async def startup_event():
    if os.getenv("API_KEY") is None:
        raise RuntimeError("API_KEY environment variable not set")
    os.makedirs("videos", exist_ok=True)
    os.makedirs("gifs", exist_ok=True)


@app.post("/jobs", status_code=202)
async def create_job(
    fps: int = Form(10),
    file: UploadFile = File(...),
    api_key: str = Depends(get_api_key)
):
    if fps <= 0:
        raise HTTPException(
            status_code=400, detail="fps must be a positive integer")
    ext = os.path.splitext(file.filename)[1]
    if not ext:
        ext = ".mp4"
    job_id = str(uuid.uuid4())
    input_path = os.path.join("videos", f"{job_id}{ext}")
    output_path = os.path.join("gifs", f"{job_id}.gif")
    with open(input_path, "wb") as buffer:
        while True:
            chunk = await file.read(1024 * 1024)
            if not chunk:
                break
            buffer.write(chunk)
    with jobs_lock:
        jobs[job_id] = {
            "status": "queued",
            "input_path": input_path,
            "output_path": output_path,
            "error": None
        }
    thread = threading.Thread(target=process_video,
                              args=(job_id, fps), daemon=True)
    thread.start()
    return {"job_id": job_id}


@app.get("/jobs/{job_id}")
async def get_job_status(
    job_id: str,
    request: Request,
    api_key: str = Depends(get_api_key)
):
    with jobs_lock:
        job = jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    response = {"job_id": job_id, "status": job["status"]}
    if job["status"] == "failed":
        response["error"] = job["error"]
    if job["status"] == "finished":
        response["download_url"] = request.url_for(
            "get_job_result", job_id=job_id)
    return response


@app.get("/jobs/{job_id}/gif")
async def get_job_result(
    job_id: str,
    api_key: str = Depends(get_api_key)
):
    with jobs_lock:
        job = jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job["status"] != "finished":
        raise HTTPException(status_code=400, detail="Job not finished")
    return FileResponse(path=job["output_path"], media_type="image/gif", filename=f"{job_id}.gif")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000)
