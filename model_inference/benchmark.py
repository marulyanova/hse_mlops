import requests
import time
import argparse
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

metrics_collector = {"cpu_samples": [], "memory_samples": [], "stop_monitoring": False}


def monitor_resources(url_base, interval=1.0):
    # Фоновый поток для сбора метрик CPU/RAM с сервера
    metrics_url = f"{url_base}/metrics"
    while not metrics_collector["stop_monitoring"]:
        try:
            resp = requests.get(metrics_url, timeout=2)
            if resp.status_code == 200:
                data = resp.json()
                metrics_collector["cpu_samples"].append(data.get("cpu_percent", 0))
                metrics_collector["memory_samples"].append(data.get("memory_mb", 0))
        except Exception:
            pass
        time.sleep(interval)


def send_request(url, text):
    start = time.time()
    try:
        resp = requests.post(url, json={"text": text}, timeout=30)
        end = time.time()
        if resp.status_code == 200:
            return end - start, True
        else:
            return end - start, False
    except Exception:
        return 0, False


def run_benchmark(port, concurrency, num_requests):
    url_base = f"http://localhost:{port}"
    url_embed = f"{url_base}/embed"
    test_text = "Тестовый запрос для замера производительности модели abacaba" * 5

    metrics_collector["cpu_samples"] = []
    metrics_collector["memory_samples"] = []
    metrics_collector["stop_monitoring"] = False

    print(
        f"Запуск бенчмарка: порт {port}, потоки {concurrency}, запросы {num_requests}"
    )

    monitor_thread = threading.Thread(target=monitor_resources, args=(url_base, 0.5))
    monitor_thread.start()

    start_total = time.time()
    latencies = []
    success_count = 0

    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = [
            executor.submit(send_request, url_embed, test_text)
            for _ in range(num_requests)
        ]

        for i, future in enumerate(as_completed(futures)):
            latency, success = future.result()
            if success:
                latencies.append(latency)
                success_count += 1

            if (i + 1) % 10 == 0:
                print(f"Выполнено запросов: {i + 1}/{num_requests}", end="\r")

    total_time = time.time() - start_total

    metrics_collector["stop_monitoring"] = True
    monitor_thread.join()

    cpu_avg = (
        sum(metrics_collector["cpu_samples"]) / len(metrics_collector["cpu_samples"])
        if metrics_collector["cpu_samples"]
        else 0
    )
    mem_avg = (
        sum(metrics_collector["memory_samples"])
        / len(metrics_collector["memory_samples"])
        if metrics_collector["memory_samples"]
        else 0
    )
    mem_max = (
        max(metrics_collector["memory_samples"])
        if metrics_collector["memory_samples"]
        else 0
    )

    if latencies:
        avg_latency = sum(latencies) / len(latencies)
        min_latency = min(latencies)
        max_latency = max(latencies)
        throughput = success_count / total_time
    else:
        avg_latency = min_latency = max_latency = throughput = 0

    print(f"Всего запросов: {num_requests}, успешных: {success_count}")
    print(f"Общее время теста: {total_time:.1f} сек")
    print(f"Throughput (RPS): {throughput:.1f}")
    print(f"Latency Avg: {avg_latency*1000:.1f} ms")
    print(f"Latency Min: {min_latency*1000:.1f} ms")
    print(f"Latency Max: {max_latency*1000:.1f} ms")
    print(f"CPU Usage (Avg): {cpu_avg:.1f} %")
    print(f"RAM Usage (Avg): {mem_avg:.1f} MB")
    print(f"RAM Usage (Max): {mem_max:.1f} MB")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8001)
    parser.add_argument(
        "--concurrency", type=int, default=1, help="Количество параллельных потоков"
    )
    parser.add_argument(
        "--num_requests", type=int, default=50, help="Количество запросов"
    )
    args = parser.parse_args()

    run_benchmark(args.port, args.concurrency, args.num_requests)
