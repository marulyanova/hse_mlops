import psutil
import os
import asyncio
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from transformers import AutoTokenizer
from optimum.onnxruntime import ORTModelForFeatureExtraction

import time
import numpy as np

app = FastAPI()
process = psutil.Process(os.getpid())

MAX_BATCH_SIZE = 16
MAX_WAIT_TIME = 0.1  # максимальное время ожидания накопления батча

model_path = "./onnx_model"
model = ORTModelForFeatureExtraction.from_pretrained(model_path)
tokenizer = AutoTokenizer.from_pretrained(model_path)

request_queue = asyncio.Queue()


class TextRequest(BaseModel):
    text: str


def process_batch(texts):
    inputs = tokenizer(
        texts, return_tensors="np", padding=True, truncation=True, max_length=512
    )
    outputs = model(**inputs)
    embeddings = outputs.last_hidden_state.mean(axis=1)
    return embeddings


async def batch_worker():
    while True:
        batch = []
        futures = []

        # ожидание первого запроса
        try:
            first_item = await asyncio.wait_for(
                request_queue.get(), timeout=MAX_WAIT_TIME
            )
            batch.append(first_item[0])
            futures.append(first_item[1])
        except asyncio.TimeoutError:
            continue

        # пытаемся добрать запросы до лимита размера MAX_BATCH_SIZE или времени MAX_WAIT_TIMEы
        start_time = time.time()
        while len(batch) < MAX_BATCH_SIZE:
            time_left = MAX_WAIT_TIME - (time.time() - start_time)
            if time_left <= 0:
                break
            try:
                item = await asyncio.wait_for(request_queue.get(), timeout=time_left)
                batch.append(item[0])
                futures.append(item[1])
            except asyncio.TimeoutError:
                break

        # инференс одним вызовом
        try:
            results = process_batch(batch)
            # возврат результатов ожидающим запросам
            for i, future in enumerate(futures):
                if not future.done():
                    future.set_result(results[i].tolist())
        except Exception as e:
            for future in futures:
                if not future.done():
                    future.set_exception(e)


@app.on_event("startup")
async def startup_event():
    asyncio.create_task(batch_worker())


@app.post("/embed")
async def get_embedding(request: TextRequest):
    loop = asyncio.get_event_loop()
    future = loop.create_future()

    await request_queue.put((request.text, future))

    try:
        result = await future
        return {
            "embedding": result,
            "latency_sec": 0,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/metrics")
async def get_metrics():
    cpu = process.cpu_percent(interval=0.1)
    memory = process.memory_info().rss / 1024 / 1024
    return {"cpu_percent": cpu, "memory_mb": memory}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8003)
