import re
import subprocess
import threading
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from time import sleep

import requests
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

REPO = "S-furi/er-climate-monitor-dsl"
RELEASE_VERSION = "v0.2.6"
JAR_NAME = f"sensorDsl-{RELEASE_VERSION}.jar"
IMAGE_VERSION = "1.0.4"
EDITOR_IMAGE = f"sfuri/er-climate-monitor-dsl-editor:{IMAGE_VERSION}"
EDITOR_PORT = 8080


@asynccontextmanager
async def lifespan(app: FastAPI):
    threading.Thread(target=lambda: start_web_editor(), daemon=True).start()
    yield
    global docker_container_id
    try:
        if docker_container_id:
            subprocess.run(
                ["docker", "rm", "-f", docker_container_id],
                capture_output=True,
                check=False,
            )
    except Exception as _:
        pass


app = FastAPI(lifespan=lifespan)

app.mount("/static", StaticFiles(directory="static"), name="static")

docker_container_id = None


class CodeRequest(BaseModel):
    code: str


def download_jar():
    path = Path(f"/tmp/{JAR_NAME}")
    if path.exists():
        return str(path)

    try:
        url = f"https://api.github.com/repos/{REPO}/releases/latest"
        res = requests.get(url)
        res.raise_for_status()

        data = res.json()
        jar_url = None
        for asset in data.get("assets", []):
            if asset["name"].endswith("jar"):
                jar_url = asset["browser_download_url"]
                break

        if not jar_url:
            raise Exception("No JAR fil found in latest release")

        print(f"Downloading JAR from {jar_url}")
        jar_res = requests.get(jar_url)
        jar_res.raise_for_status()

        with open(path, "wb") as f:
            f.write(jar_res.content)

        return str(path)

    except Exception as e:
        print(f"Error downloading jar: {e}")
        raise HTTPException(status_code=500, detail=f"Error downloading jar: {e}")


def start_web_editor():
    global docker_container_id

    try:
        if docker_container_id:
            subprocess.run(
                ["docker", "rm", "-f", docker_container_id],
                capture_output=True,
                check=False,
            )

        res = subprocess.run(
            ["docker", "run", "-d", "-p", f"{EDITOR_PORT}:8080", EDITOR_IMAGE],
            capture_output=True,
            text=True,
            check=True,
        )
        docker_container_id = res.stdout.strip()
        sleep(2)
    except subprocess.CalledProcessError as e:
        print(f"Error starting editor container: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start editor! {e}")


@app.get("/", response_class=HTMLResponse)
async def serve_root():
    with open("index.html", "r") as f:
        html_content = f.read()
    return HTMLResponse(content=html_content)


@app.post("/generate-sensor")
async def generate_sensor(request: CodeRequest):
    if not request.code.strip():
        raise HTTPException(status_code=400, detail="Code cannot be empty!")
    try:
        jar_path = download_jar()
        name = re.search(r"name\s\"(.*)\"", request.code, re.M)

        if name is None:
            name = str(uuid.uuid4())
        else:
            name = name[1].strip().lower().replace(" ", "_")

        base = Path(".")
        input_file_path = (base / f"{name}.uanciutri").resolve()
        output_path = base.resolve()

        with open(input_file_path, "w") as f:
            f.write(request.code)

        java_cmd = ["java", "-jar", jar_path, str(input_file_path), str(output_path)]
        result = subprocess.run(java_cmd, capture_output=True, text=True, timeout=5)

        if result.returncode != 0:
            raise Exception(f"Conversion failed: ${result.stderr}")

        return JSONResponse(
            {
                "success": True,
                "message": "Sensor generated succesfully",
                "outpu": result.stdout,
                "name": name,
            }
        )

    except Exception as e:
        print(f"An error occurred while generating sensor: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    if docker_container_id is None:
        return {"status": "Creating"}
    else:
        return {
            "status": "healthy",
            "port": EDITOR_PORT,
            "container_id": docker_container_id,
        }


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8880)
