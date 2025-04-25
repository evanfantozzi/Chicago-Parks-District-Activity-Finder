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

RUN pip install --no-cache-dir -r requirements.txt

RUN echo "SELECT load_extension('mod_spatialite');" | sqlite3 :memory:

ENV SPATIALITE_PATH=/usr/lib/x86_64-linux-gnu/mod_spatialite.so

EXPOSE 10000

CMD ["gunicorn", "app:app"]
