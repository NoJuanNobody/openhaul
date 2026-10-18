FROM python:3.11-slim
WORKDIR /app
COPY python/ /app/python/
RUN pip install --no-cache-dir numpy scipy
CMD ["python3", "python/chaos_sim/runner.py"]
