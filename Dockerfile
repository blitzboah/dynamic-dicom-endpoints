FROM python:3.9-slim

# Install dcmtk for DICOM-related operations
RUN apt-get update && apt-get install -y \
    dcmtk \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user for security
RUN useradd -m appuser
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    rm -rf ~/.cache/pip

# Copy all the application code
COPY . .

# Set user to non-root
USER appuser

# Expose Flask port
EXPOSE 5000

# By default, run the CLI
ENTRYPOINT ["python", "main.py"]
CMD []
