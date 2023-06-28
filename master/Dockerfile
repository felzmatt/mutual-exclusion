# Use an official Python runtime as the base image
FROM python:3.9

# Set the working directory in the container
WORKDIR /app


# Copy the requirements.txt file to the container
# COPY requirements.txt .

# Install the Python dependencies
# RUN pip install --no-cache-dir -r requirements.txt

# copy dependencies
COPY ../common /app/common

# Copy executables
COPY ../master.py /app


CMD ["python3", "-u", "master.py"]