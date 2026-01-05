# Stage 1: Build frontend
FROM node:20-slim AS frontend-builder
WORKDIR /app/web_frontend
COPY web_frontend/package*.json ./
RUN npm ci
COPY web_frontend/ ./
RUN npm run build

# Stage 2: Python backend with frontend assets
FROM python:3.12-slim
WORKDIR /app

# Install system dependencies (libpq5 for psycopg2, git for pip git dependencies)
RUN apt-get update && apt-get install -y libpq5 git && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Copy built frontend from stage 1
COPY --from=frontend-builder /app/web_frontend/dist ./web_frontend/dist

# Run the application (use PORT env var from Railway, default to 8000)
CMD ["sh", "-c", "python main.py --port ${PORT:-8000}"]
