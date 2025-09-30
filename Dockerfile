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

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Confirm mod_spatialite loads
RUN echo "SELECT load_extension('/usr/lib/x86_64-linux-gnu/mod_spatialite');" | sqlite3 :memory:

# Set extension path for use in app
ENV SPATIALITE_PATH=/usr/lib/x86_64-linux-gnu/mod_spatialite

EXPOSE 10000

# Start Flask app
CMD ["gunicorn", "app.app:app"]
