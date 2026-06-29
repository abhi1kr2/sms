# Base image
FROM python:3.12-slim

# Set Container working directory
WORKDIR /app

# Copy dependency files
COPY requirements .

# Install dependencies
RUN pip install --no-cache-dir -r requirements

# Copy project files
COPY . /app

# Expose port for Flask
EXPOSE 5000

# Run Flask app with Gunicorn / Production server
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]