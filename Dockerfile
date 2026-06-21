# DataNarrate Full-Stack Container (Python Backend + Node.js Remotion)
# Render.com deployment — single image with Python + Node.js

# ── Stage 1: Base image ───────────────────────────────────────────────────────
FROM python:3.10-slim

# ── Stage 2: System dependencies (ffmpeg, chromium for Remotion/Puppeteer) ───
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl ffmpeg procps \
        chromium libnss3 libatk-bridge2.0-0 libxcomposite1 \
        libxrandr2 libgbm1 libasound2 && \
    rm -rf /var/lib/apt/lists/*

# ── Stage 3: Node.js 18 LTS ──────────────────────────────────────────────────
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - && \
    apt-get install -y --no-install-recommends nodejs && \
    rm -rf /var/lib/apt/lists/*

# ── Stage 4: Working directory ───────────────────────────────────────────────
WORKDIR /app

# ── Stage 5: Python dependencies (cached layer) ──────────────────────────────
COPY backend/requirements.txt ./backend/
RUN pip install --no-cache-dir -r ./backend/requirements.txt

# ── Stage 6: Node/Remotion dependencies (cached layer) ───────────────────────
COPY remotion/package.json remotion/package-lock.json ./remotion/
RUN cd remotion && npm ci

# ── Stage 7: Copy ALL project files into /app ─────────────────────────────────
# This single command guarantees /app/remotion, /app/backend, /app/api, etc.
# all land exactly where Python's Path(__file__) resolution expects them.
COPY . .

# ── Stage 8: Verify the directory structure at build time (sanity check) ──────
RUN echo "=== /app structure ===" && ls -la /app && \
    echo "=== /app/remotion ===" && ls /app/remotion

# ── Stage 9: Runtime environment ─────────────────────────────────────────────
ENV PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true
ENV PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium

# Run uvicorn from the backend directory
WORKDIR /app/backend
CMD ["python", "main.py"]
