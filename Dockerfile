# Use official Python runtime as a parent image
FROM python:3.9-slim

# Install system dependencies (Tesseract OCR + Japanese language pack)
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-jpn \
    tesseract-ocr-eng \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Copy requirements and install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Create directories for upload/process to avoid permissions issues
RUN mkdir -p uploads processed_web

# Expose the port (Render uses $PORT environment variable)
ENV PORT=5555
EXPOSE $PORT

# Run the app using Gunicorn
# "app:app" means "module 'app':variable 'app'"
CMD gunicorn --bind 0.0.0.0:$PORT --workers 1 --threads 4 --timeout 120 app:app
