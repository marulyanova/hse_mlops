import psutil
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
import time

app = FastAPI()
process = psutil.Process(os.getpid())

model = SentenceTransformer("sergeyzh/rubert-mini-frida", device="cpu")


class TextRequest(BaseModel):
    text: str


@app.post("/embed")
async def get_embedding(request: TextRequest):
    start_time = time.time()
    try:
        embedding = model.encode([request.text], convert_to_numpy=True)[0]
        latency = time.time() - start_time
        return {"embedding": embedding.tolist(), "latency_sec": latency}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/metrics")
async def get_metrics():
    cpu = process.cpu_percent(interval=0.1)
    memory = process.memory_info().rss / 1024 / 1024  # в мегабайт
    return {"cpu_percent": cpu, "memory_mb": memory}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
