# gunicorn.conf.py
timeout = 300           # 5 minutes
graceful_timeout = 60   # 60 seconds for workers to finish
workers = 2             # keep low to avoid memory issues on free tier
threads = 2