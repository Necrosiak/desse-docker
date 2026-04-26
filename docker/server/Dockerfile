# =============================================================================
# NetworkMemories — Demon's Souls Server
# Python 3.11 slim — pycryptodome (Python 3 maintained fork of pycrypto)
# =============================================================================
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy server files
COPY emulator.py .
COPY emu/ ./emu/
COPY data/ ./data/

# Create persistent DB directory
RUN mkdir -p /app/db

# Non-root user for security
RUN useradd -r -s /bin/false desse && chown -R desse:desse /app
USER desse

EXPOSE 18000

CMD ["python", "-u", "emulator.py"]
