FROM python:3.11-slim

# Install system dependencies including libspatialite
RUN apt-get update && apt-get install -y \
  gcc \
  g++ \
  make \
  libsqlite3-dev \
  libgeos-dev \
  libproj-dev \
  libxml2-dev \
  libfreexl-dev \
  libreadline-dev \
  libcurl4-gnutls-dev \
  libspatialite-dev \
  wget \
  sqlite3 \
  && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy your app code into the image
COPY . .

# Download your hosted video from Google Drive into /static
RUN mkdir -p static && \
    wget --no-check-certificate \
    "https://drive.google.com/uc?export=download&id=1NRg29suCuBUpzDx2ShO5GyWx08jDeBz_" \
    -O static/video.mp4

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Directly test known mod_spatialite path (skip symlink logic)
RUN echo "SELECT load_extension('/usr/lib/x86_64-linux-gnu/mod_spatialite.so');" | sqlite3 :memory:

# Set path for use in Python
ENV SPATIALITE_PATH=/usr/lib/x86_64-linux-gnu/mod_spatialite.so

# Expose port for local dev (Render doesn't need this)
EXPOSE 10000

# Start Flask app
CMD ["gunicorn", "app:app"]
