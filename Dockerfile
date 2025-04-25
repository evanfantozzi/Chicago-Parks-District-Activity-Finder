FROM python:3.11-slim

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

# Minimal working dir just for testing
WORKDIR /app
COPY . .

# ✅ List all mod_spatialite files
RUN find / -name "mod_spatialite*" || true

CMD ["echo", "Check the build logs for mod_spatialite paths."]
