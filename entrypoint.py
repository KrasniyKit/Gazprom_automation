import subprocess
import time
import os
import urllib.request
import json

OLLAMA_HOST_URL = os.getenv("OLLAMA_HOST", "http://ollama:11434")
MODEL_NAME = os.getenv("OLLAMA_MODEL", "qwen2.5vl:7b")
JSON_HEADERS = {"Content-Type": "application/json"}

print(f"⏳ Waiting for Ollama server at {OLLAMA_HOST_URL}...")
while True:
    try:
        urllib.request.urlopen(f"{OLLAMA_HOST_URL}/api/tags")
        break
    except Exception:
        time.sleep(2)

try:
    tags_response = urllib.request.urlopen(f"{OLLAMA_HOST_URL}/api/tags")
    tags_payload = json.loads(tags_response.read().decode("utf-8"))
    installed_models = {m.get("name") for m in tags_payload.get("models", []) if m.get("name")}
except Exception as e:
    installed_models = set()
    print(f"Warning: Could not fetch installed Ollama models: {e}")

if MODEL_NAME not in installed_models:
    print(f"✅ Ollama is up. Pulling model {MODEL_NAME} (this may take time on first run)...")
    try:
        pull_data = json.dumps({"name": MODEL_NAME, "stream": False}).encode("utf-8")
        req = urllib.request.Request(
            f"{OLLAMA_HOST_URL}/api/pull",
            data=pull_data,
            headers=JSON_HEADERS,
            method="POST",
        )
        pull_response = urllib.request.urlopen(req)
        pull_response.read()
    except Exception as e:
        print(f"Warning: Could not pull model automatically: {e}")
else:
    print(f"✅ Ollama is up. Model {MODEL_NAME} is already available.")

print("🚀 Starting FastAPI application...")
subprocess.run(["poetry", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"])
