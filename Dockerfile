FROM ubuntu:22.04

# Install system libraries and mod_spatialite
RUN apt-get update && apt-get install -y \
  python3.11 \
  python3.11-venv \
  python3-pip \
  gcc \
  g++ \
  make \
  wget \
  sqlite3 \
  libsqlite3-mod-spatialite \
  && rm -rf /var/lib/apt/lists/*

# Set up working directory
WORKDIR /app

COPY . .

# Download your hosted video
RUN mkdir -p static && \
    wget --no-check-certificate \
    "https://drive.google.com/uc?export=download&id=1NRg29suCuBUpzDx2ShO5GyWx08jDeBz_" \
    -O static/video.mp4

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# ✅ Validate extension loads successfully from known Ubuntu path
RUN echo "SELECT load_extension('/usr/lib/x86_64-linux-gnu/mod_spatialite');" | sqlite3 :memory:

# ✅ Set path for your Python app
ENV SPATIALITE_PATH=/usr/lib/x86_64-linux-gnu/mod_spatialite

# Optional for local dev
EXPOSE 10000

# Start Flask app
CMD ["gunicorn", "app:app"]
