FROM python:3.10

# Install system dependencies including tesseract-ocr
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libtesseract-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p static/uploads/symptoms

# Expose the port the app runs on
EXPOSE 7860

# Command to run the application
CMD ["python", "app.py"]
