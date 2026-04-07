FROM python:3.11-slim

WORKDIR /app

# Install build tools needed by some Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download NLTK data so the container doesn't fetch it at runtime
RUN python -c "\
import nltk; \
nltk.download('punkt',     quiet=True); \
nltk.download('punkt_tab', quiet=True); \
nltk.download('stopwords', quiet=True)"

# Copy the rest of the source code
COPY . .

# Ensure the uploads folder exists
RUN mkdir -p uploads

# Railway injects $PORT at runtime; default to 8000 for local Docker testing
EXPOSE 8000

# Use gunicorn in production — 2 workers, 120 s timeout for large PDF uploads
CMD gunicorn --bind 0.0.0.0:${PORT:-8000} --workers 2 --timeout 120 app:app
