FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# libgomp is required by onnxruntime; curl for healthcheck
RUN apt-get update \
    && apt-get install -y --no-install-recommends libgomp1 curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY models ./models

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s \
    CMD curl -fs http://localhost:8000/docs > /dev/null || exit 1

CMD ["fastapi", "run", "app/main.py", "--host", "0.0.0.0", "--port", "8000"]

# ── GPU support (disabled) ───────────────────────────────────────────────────
# To re-enable, replace everything above with:
#
# FROM nvidia/cuda:12.4.1-cudnn-runtime-ubuntu22.04
# ENV PYTHONDONTWRITEBYTECODE=1 \
#     PYTHONUNBUFFERED=1
# WORKDIR /app
# RUN apt-get update \
#     && apt-get install -y --no-install-recommends python3 python3-pip curl libgomp1 \
#     && ln -sf /usr/bin/python3 /usr/bin/python \
#     && rm -rf /var/lib/apt/lists/*
# # Swap CPU onnxruntime for the GPU build (they conflict if both are installed)
# COPY requirements.txt .
# RUN sed -E 's/^onnxruntime$/onnxruntime-gpu/' requirements.txt > requirements.gpu.txt \
#     && pip install --no-cache-dir -r requirements.gpu.txt
# COPY app ./app
# COPY models ./models
# EXPOSE 8000
# HEALTHCHECK --interval=30s --timeout=5s --start-period=30s \
#     CMD curl -fs http://localhost:8000/docs > /dev/null || exit 1
# CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
