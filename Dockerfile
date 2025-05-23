# Use a lightweight Alpine image of Python
FROM python:3.9-alpine

# Set the working directory inside the container
WORKDIR /app

# Copy requirements and install pika
COPY requirements.txt .

# Install Python dependencies (pika only) with no cache
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY ./app/ .

# Expose port 80
EXPOSE 80

#BUID
# docker build -t sw .

# DEV
# CMD ["python", "run.py"]
# CMD ["gunicorn", "--bind", "0.0.0.0:80", "main:create_app()"] 

#HOMELAB
CMD ["gunicorn", "--bind", "0.0.0.0:80", "--workers=2", "--threads=2", "--timeout=90", "--access-logfile=-", "--error-logfile=-", "main:create_app()"]

#PRODUCTION
# CMD ["gunicorn", "--bind", "0.0.0.0:80", "--workers=4", "--threads=2", "--timeout=120", "--access-logfile=-", "--error-logfile=-", "main:create_app()"]
