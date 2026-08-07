# Use official Python image
FROM python:3.11-slim

# Set working directory
WORKDIR /main

# Copy requirements from parent folder
COPY ./requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend files
COPY . .

# Expose port
EXPOSE 8000

# Start application
CMD ["gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "main:app", "--bind", "0.0.0.0:8000"]
