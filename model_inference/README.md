# HW №3: Изучение разных уровней оптимизации inference pipeline и анализ эффектов

### Запуск

**1. Базовый инференс**

```sh
python3 base_inference.py
```

```sh
python3 benchmark.py --port 8001 --concurrency 10 --num_requests 1000
```

**2. ONNX инференс**

```sh
python3 export_onnx.py
```

```sh
python3 onnx_inference.py
```

```sh
python3 benchmark.py --port 8002 --concurrency 10 --num_requests 1000
```

**3. ONNX Batch инференс**

```sh
python3 batch_inference.py
```

```sh
python3 benchmark.py --port 8003 --concurrency 10 --num_requests 1000
```