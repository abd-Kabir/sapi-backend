# Use the official Python image from the Docker Hub
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install the dependencies from requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project into the container
COPY . .

# Set environment variables (for production use)
ENV PYTHONUNBUFFERED 1

# Expose the port Django will run on
EXPOSE 8000

# Command to run Django in production (after migrations and collectstatic)
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "config.wsgi:application"]
# CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
