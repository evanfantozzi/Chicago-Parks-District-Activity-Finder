FROM ubuntu:22.04

# Install system libraries, Python, and mod_spatialite
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

# Set working directory
WORKDIR /app

# Copy app code
COPY . .

# ✅ Install Python deps
RUN pip install --no-cache-dir -r requirements.txt

# ✅ Install gdown and download the .mp4 reliably from Google Drive
RUN pip install gdown && \
    mkdir -p static && \
    gdown --id 1NRg29suCuBUpzDx2ShO5GyWx08jDeBz_ -O static/video.mp4

# ✅ Confirm mod_spatialite loads correctly
RUN echo "SELECT load_extension('/usr/lib/x86_64-linux-gnu/mod_spatialite');" | sqlite3 :memory:

# ✅ Set for runtime use
ENV SPATIALITE_PATH=/usr/lib/x86_64-linux-gnu/mod_spatialite

# Optional: expose port
EXPOSE 10000

# ✅ Start your Flask app
CMD ["gunicorn", "app:app"]
