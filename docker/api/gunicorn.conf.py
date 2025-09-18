# Gunicorn configuration for Gopnik API server

import multiprocessing
import os

# Server socket
bind = "0.0.0.0:8000"
backlog = 2048

# Worker processes
workers = int(os.environ.get("GOPNIK_WORKERS", multiprocessing.cpu_count() * 2 + 1))
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50

# Timeout settings
timeout = 300  # 5 minutes for large file processing
keepalive = 2
graceful_timeout = 30

# Logging
accesslog = "/app/logs/access.log"
errorlog = "/app/logs/error.log"
loglevel = os.environ.get("GOPNIK_LOG_LEVEL", "info")
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = "gopnik-api"

# Server mechanics
daemon = False
pidfile = "/tmp/gopnik-api.pid"
user = "gopnik"
group = "gopnik"
tmp_upload_dir = "/app/temp"

# SSL (if certificates are provided)
keyfile = os.environ.get("GOPNIK_SSL_KEYFILE")
certfile = os.environ.get("GOPNIK_SSL_CERTFILE")

# Worker tuning
preload_app = True
worker_tmp_dir = "/dev/shm"

# Security
limit_request_line = 8192
limit_request_fields = 100
limit_request_field_size = 8190

def when_ready(server):
    """Called just after the server is started."""
    server.log.info("Gopnik API server is ready to accept connections")

def worker_int(worker):
    """Called just after a worker has been killed by a signal."""
    worker.log.info("Worker received INT or QUIT signal")

def pre_fork(server, worker):
    """Called just before a worker is forked."""
    server.log.info("Worker spawned (pid: %s)", worker.pid)

def post_fork(server, worker):
    """Called just after a worker has been forked."""
    server.log.info("Worker spawned (pid: %s)", worker.pid)

def worker_abort(worker):
    """Called when a worker receives the SIGABRT signal."""
    worker.log.info("Worker received SIGABRT signal")