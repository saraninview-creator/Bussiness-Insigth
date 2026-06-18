# ---- Base image ----
FROM python:3.13-slim

# ---- Install system deps ----
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# ---- Create app directory ----
WORKDIR /app

# ---- Install Python deps ----
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ---- Copy source code ----
COPY . .

# ---- Expose the port FastAPI runs on ----
EXPOSE 8000

# ---- Run the server ----
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
