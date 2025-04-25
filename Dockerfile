# Use a slim Python base image
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

# Find and symlink mod_spatialite.so correctly (robust version)
RUN bash -c "\
  echo '🔍 Searching for mod_spatialite .so files:' && \
  find /usr -name 'mod_spatialite*.so*' && \
  MOD_PATH=\$(find /usr -name 'mod_spatialite*.so*' | grep -E '\.so([0-9]*|$)' | head -n 1) && \
  echo '✅ Found mod_spatialite at: '\$MOD_PATH && \
  ln -sf \$MOD_PATH /usr/lib/mod_spatialite.so && \
  echo \"SELECT load_extension('/usr/lib/mod_spatialite.so');\" | sqlite3 :memory:"

# Set the path for Python to use in your app
ENV SPATIALITE_PATH=/usr/lib/mod_spatialite.so

# Optional: expose port for local dev
EXPOSE 10000

# Start the Flask app using gunicorn
CMD ["gunicorn", "app:app"]
