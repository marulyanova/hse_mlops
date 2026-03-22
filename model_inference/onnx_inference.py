import psutil
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from transformers import AutoTokenizer
from optimum.onnxruntime import ORTModelForFeatureExtraction
import time
import numpy as np

app = FastAPI()
process = psutil.Process(os.getpid())

model_path = "./onnx_model"
model = ORTModelForFeatureExtraction.from_pretrained(model_path)
tokenizer = AutoTokenizer.from_pretrained(model_path)


class TextRequest(BaseModel):
    text: str


def get_embedding_onnx(text):
    inputs = tokenizer(
        text, return_tensors="np", padding=True, truncation=True, max_length=512
    )

    outputs = model(**inputs)
    embeddings = outputs.last_hidden_state.mean(axis=1)
    return embeddings[0]


@app.post("/embed")
async def get_embedding(request: TextRequest):
    start_time = time.time()
    try:
        embedding = get_embedding_onnx(request.text)
        latency = time.time() - start_time
        return {"embedding": embedding.tolist(), "latency_sec": latency}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/metrics")
async def get_metrics():
    cpu = process.cpu_percent(interval=0.1)
    memory = process.memory_info().rss / 1024 / 1024
    return {"cpu_percent": cpu, "memory_mb": memory}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8002)
