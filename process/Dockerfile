# Use an official Python runtime as the base image
FROM python:3.9

# Set the working directory in the container
WORKDIR /app


# Copy the requirements.txt file to the container
# COPY requirements.txt .

# Install the Python dependencies
# RUN pip install --no-cache-dir -r requirements.txt
RUN apt-get update && apt-get install -y dnsutils net-tools


# copy dependencies
COPY ../algorithms /app/algorithms
COPY ../common /app/common

# Copy executables
COPY ../process.py .
COPY ../entrypoint.sh .




