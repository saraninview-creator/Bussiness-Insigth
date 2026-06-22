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
# This captures 'remotion_project', 'backend', 'api', etc.
COPY . .

# ── Stage 7: Install Node/Remotion dependencies AFTER copy ───────────────────
# Ensuring we use the new 'remotion_project' folder name
RUN cd /app/remotion_project && npm ci

# ── Stage 8: Build-time verification ─────────────────────────────────────────
RUN echo "=== /app structure ===" && ls -la /app && \
    echo "=== /app/remotion_project ===" && ls /app/remotion_project && \
    echo "=== remotion_project/node_modules present ===" && ls /app/remotion_project/node_modules | head -5

# ── Stage 9: Runtime environment ─────────────────────────────────────────────
ENV PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true
ENV PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium

# Run uvicorn from the root to ensure os.getcwd() is /app
# This aligns with the dynamic path resolution in pipeline.py
CMD ["python", "backend/main.py"]
