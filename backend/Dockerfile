FROM python:3.12-slim

WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create uploads directory
RUN mkdir -p uploads

# Expose port
EXPOSE 8001

# Start command - CORRECT PATH: src.app.main:app
CMD ["uvicorn", "src.app.main:app", "--host", "0.0.0.0", "--port", "8001"]
