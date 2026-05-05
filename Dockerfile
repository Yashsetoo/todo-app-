# Use an official Python runtime as the base 
FROM python:3.11-slim 
# Set the working directory inside the container 
WORKDIR /app 
# Copy requirements first (Docker caches this layer separately) 
# If requirements.txt hasn't changed, Docker reuses the cached layer 
COPY requirements.txt . 
# Install dependencies 
RUN pip install --no-cache-dir -r requirements.txt 
# Copy the rest of the application code 
COPY . . 
# Expose the port the app runs on 
EXPOSE 8000 
# Command to run the app using gunicorn (production server) 
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--timeout", "600", "app:app"]