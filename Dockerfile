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

# ── Stage 6: Copy ALL project files into /app FIRST ──────────────────────────
# CRITICAL ORDER: COPY . . must come BEFORE npm ci.
# Previously npm ci ran first and COPY . . second — the COPY overwrote
# /app/remotion/ with the git-tracked version (empty node_modules because
# node_modules/ is in .gitignore). This caused: [Errno 2] No such file /remotion
COPY . .

# ── Stage 7: Install Node/Remotion dependencies AFTER copy ───────────────────
# npm ci now installs into /app/remotion/node_modules and nothing overwrites it.
RUN cd /app/remotion && npm ci

# ── Stage 8: Build-time verification (hard fail if /app/remotion is missing) ──
RUN echo "=== /app structure ===" && ls -la /app && \
    echo "=== /app/remotion ===" && ls /app/remotion && \
    echo "=== remotion/node_modules present ===" && ls /app/remotion/node_modules | head -5 && \
    echo "=== Resolved remotion path from pipeline.py ===" && \
    python3 -c "import os; f='/app/backend/pipeline.py'; print(os.path.abspath(os.path.join(os.path.dirname(f), '..', 'remotion')))"

# ── Stage 9: Runtime environment ─────────────────────────────────────────────
ENV PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true
ENV PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium

# Run uvicorn from /app/backend
WORKDIR /app/backend
CMD ["python", "main.py"]
