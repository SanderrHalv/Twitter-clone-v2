# Dockerfile

FROM python:3.11-slim

# 1) Set a working directory
WORKDIR /app

# 2) Install system dependencies and create a non-root user
RUN apt-get update \
 && apt-get install -y --no-install-recommends gcc libpq-dev \
 && rm -rf /var/lib/apt/lists/*

# 3) Copy only requirements first (for layer caching)
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# 4) Copy app code
COPY . .

# 5) Expose port and set env defaults
ENV PORT=8000
EXPOSE 8000

# 6) Healthcheck (optional)
HEALTHCHECK --interval=30s --timeout=5s \
  CMD curl -f http://localhost:$PORT/health || exit 1

# 7) Launch via Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
