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

# Copy application code and static assets
COPY main.py .
COPY static/ ./static/
COPY skills/ ./skills/
COPY data/ ./data/

# Copy knowledge base if present (optional)
COPY KNOWLEDGE.md* ./

# Runtime data dirs (SQLite DB and audio cache)
# /data/artists is the default ARTISTS_DIR — mount a Railway volume at /data for persistence
RUN mkdir -p audio_cache static/temp_audio /data/artists

EXPOSE 8765

ENV MAESTRO_DIR=/app

# $PORT is injected by Railway; falls back to 8765 for local use
CMD ["sh", "-c", "exec uvicorn main:app --host 0.0.0.0 --port $PORT"]
