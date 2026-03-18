FROM python:3.12-slim

# System deps: ffmpeg (Whisper), libsndfile (soundfile), build tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libsndfile1 \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies first (layer cache)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy Kokoro model files (large — separate layer so code changes don't re-copy them)
COPY kokoro-v1.0.onnx voices-v1.0.bin ./

# Copy application code and static assets
COPY main.py .
COPY static/ ./static/
COPY skills/ ./skills/
COPY data/ ./data/

# Copy knowledge base if present (optional — won't fail if missing)
COPY KNOWLEDGE.md* ./

# Runtime data dirs (SQLite DB and audio cache) — use a Railway volume for persistence
RUN mkdir -p audio_cache static/temp_audio data/artists

EXPOSE 8765

ENV MAESTRO_DIR=/app

CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8765"]
