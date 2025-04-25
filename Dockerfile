# Base image with Python
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

# Copy everything into container
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Locate and symlink mod_spatialite.so (important!)
RUN find /usr -name "mod_spatialite*.so*" -exec echo Found: {} \; && \
    ln -sf $(find /usr -name "mod_spatialite*.so*" | head -n 1) /usr/lib/mod_spatialite.so && \
    echo "SELECT load_extension('/usr/lib/mod_spatialite.so');" | sqlite3 :memory:

# Pass the .so path to your Python code
ENV SPATIALITE_PATH=/usr/lib/mod_spatialite.so

# Expose (optional for local dev)
EXPOSE 10000

# Start the app
CMD ["gunicorn", "app:app"]
