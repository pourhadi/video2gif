FROM python:3.10-slim

# Install ffmpeg
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY main.py .

# Set API key environment variable (override at runtime)
ENV API_KEY=YOUR_SECURE_API_KEY_HERE
# Default port for the application; Cloud Run will override PORT automatically (typically 8080)
ENV PORT=8080
EXPOSE 8080

# Start the server, binding to the PORT environment variable
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT}"]