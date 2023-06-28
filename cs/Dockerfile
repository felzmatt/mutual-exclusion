# Use the official Python base image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file to the working directory

# Install the Python dependencies

# Copy the Flask application files to the working directory
COPY . .

RUN pip install --no-cache-dir -r requirements.txt

# Expose the port that the Flask application will be running on
EXPOSE 5000

# Set the command to run the Flask application
CMD ["python", "app.py", "--host", "0.0.0.0", "--port", "5000"]
