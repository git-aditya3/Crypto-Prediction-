FROM python:3.11-slim

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONPATH=/app/src

EXPOSE 8000 8501

# Web dashboard + REST API on :8000 (pretrained models bundled - no training needed)
CMD ["python", "run.py", "serve", "--host", "0.0.0.0", "--port", "8000"]
