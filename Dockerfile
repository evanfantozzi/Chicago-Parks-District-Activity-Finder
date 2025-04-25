FROM python:3.11-slim

# Install dependencies and build tools
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

WORKDIR /app

COPY . .

# Pull in your .mp4 from Drive
RUN mkdir -p static && \
    wget --no-check-certificate \
    "https://drive.google.com/uc?export=download&id=1NRg29suCuBUpzDx2ShO5GyWx08jDeBz_" \
    -O static/video.mp4

RUN pip install --no-cache-dir -r requirements.txt

# ✅ Use the default .so path installed by libspatialite-dev
# (This is where mod_spatialite ends up when built with SQLite extension support)
RUN echo "SELECT load_extension('/usr/lib/x86_64-linux-gnu/mod_spatialite.so');" | sqlite3 :memory:

ENV SPATIALITE_PATH=/usr/lib/x86_64-linux-gnu/mod_spatialite.so

EXPOSE 10000

CMD ["gunicorn", "app:app"]
