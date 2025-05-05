# Use the official Python image from the Docker Hub
FROM python:3.13-slim

# Install cron and other required system packages
RUN apt-get update && \
    apt-get install -y --no-install-recommends cron && \
    rm -rf /var/lib/apt/lists/*

# Set the working directory in the container
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

# Set environment variables (for production use)
ENV PYTHONUNBUFFERED 1

# Expose the port Django will run on
#EXPOSE 8000

# Command to run Django in production (after migrations and collectstatic)
#ENTRYPOINT ["docker-entrypoint.sh"]
