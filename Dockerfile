# Use a slim Python base image
FROM python:3.11-slim

# Install system packages including libspatialite
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

# Copy app code into container
COPY . .

# Download your hosted video (Google Drive direct link workaround)
RUN mkdir -p static && \
    wget --no-check-certificate \
    "https://drive.google.com/uc?export=download&id=1NRg29suCuBUpzDx2ShO5GyWx08jDeBz_" \
    -O static/video.mp4

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Find and symlink mod_spatialite.so properly (safe shell quoting)
RUN bash -c "\
  MOD_PATH=\$(find /usr -name 'mod_spatialite.so*' | grep -E '\.so(\.|$)' | head -n 1) && \
  echo 'Found mod_spatialite at: '\$MOD_PATH && \
  ln -sf \$MOD_PATH /usr/lib/mod_spatialite.so && \
  echo \"SELECT load_extension('/usr/lib/mod_spatialite.so');\" | sqlite3 :memory:"

# Make path available in your Python app
ENV SPATIALITE_PATH=/usr/lib/mod_spatialite.so

# Expose port (optional — Render handles this)
EXPOSE 10000

# Start Flask app via gunicorn
CMD ["gunicorn", "app:app"]
