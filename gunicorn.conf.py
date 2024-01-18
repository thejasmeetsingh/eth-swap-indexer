import os
import multiprocessing

PORT = os.getenv("PORT", "8000")

bind = f"0.0.0.0:{PORT}"
worker_class = "eth_swap_indexer.workers.UvicornWorker"
workers = multiprocessing.cpu_count() * 2
accesslog = "-"