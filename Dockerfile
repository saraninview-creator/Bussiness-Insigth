# DataNarrate Full-Stack Container (Python Backend + Node.js Remotion)
# Perfect for Render.com deployment

# 1. Base Image: Python 3.10 slim for efficient resource usage
FROM python:3.10-slim

# 2. Install essential system libraries, curl, and ffmpeg (vital for edge-tts and Remotion)
RUN apt-get update && \
    apt-get install -y curl ffmpeg procps chromium \
    libnss3 libatk-bridge2.0-0 libxcomposite1 \
    libxrandr2 libgbm1 libasound2 \
    && rm -rf /var/lib/apt/lists/*

# 3. Install Node.js 18+ (LTS) globally inside the same container
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - && \
    apt-get install -y nodejs

# 4. Set the general working directory
WORKDIR /app

# 5. Bring in Python Dependencies and install globally
COPY backend/requirements.txt ./backend/
RUN pip install --no-cache-dir -r ./backend/requirements.txt

# 6. Bring in Node/Remotion Dependencies and install
COPY remotion/package.json remotion/package-lock.json ./remotion/
RUN cd remotion && npm ci

# 7. Copy all actual application logic
COPY backend/ ./backend/
COPY remotion/ ./remotion/

# 8. Set up execution logic: Bind to dynamic PORT & uvicorn from backend
WORKDIR /app/backend
ENV PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true
ENV PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium

# This triggers the uvicorn hook we wrote, running the backend and waiting for tasks.
CMD ["python", "main.py"]
