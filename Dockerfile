FROM python:3.11-slim

# Install system packages including mod_spatialite
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
  spatialite-bin \
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

# Test loading mod_spatialite (no .so extension)
RUN echo "SELECT load_extension('/usr/lib/x86_64-linux-gnu/mod_spatialite');" | sqlite3 :memory:

# Set path for Python usage (no .so extension!)
ENV SPATIALITE_PATH=/usr/lib/x86_64-linux-gnu/mod_spatialite

# Optional: expose port
EXPOSE 10000

# Start the Flask app via gunicorn
CMD ["gunicorn", "app:app"]
