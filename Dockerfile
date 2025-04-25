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
  wget \
  sqlite3 \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY . .

RUN mkdir -p static && \
    wget --no-check-certificate \
    "https://drive.google.com/uc?export=download&id=1NRg29suCuBUpzDx2ShO5GyWx08jDeBz_" \
    -O static/video.mp4

RUN pip install --no-cache-dir -r requirements.txt

RUN sh -c '\
  echo "🔍 Searching for mod_spatialite .so files:" && \
  find /usr -name "mod_spatialite*.so*" && \
  MOD_PATH=$(find /usr -name "mod_spatialite*.so*" | grep -E "\.so([0-9]*|$)" | head -n 1) && \
  echo "✅ Found mod_spatialite at: $MOD_PATH" && \
  ln -sf "$MOD_PATH" /usr/lib/mod_spatialite.so && \
  echo "SELECT load_extension(\"/usr/lib/mod_spatialite.so\");" | sqlite3 :memory:'

ENV SPATIALITE_PATH=/usr/lib/mod_spatialite.so

EXPOSE 10000

CMD ["gunicorn", "app:app"]
