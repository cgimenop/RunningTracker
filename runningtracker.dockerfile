# Use official Python slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy the script into the container
COPY src/trainparser.py /app/trainparser.py
COPY requirements.txt /app/requirements.txt

# Install system dependencies needed for pandas & MongoDB driver
RUN apt-get update && apt-get install -y --no-install-recommends gcc && rm -rf /var/lib/apt/lists/*

# Install python dependencies
RUN pip install -r requirements.txt --no-cache-dir

# Default command to run the parser with --help (change as needed)
# CMD ["python", "trainparser.py", "-h"]

#Build image
# docker build -t tcx-parser:latest .

#run w files or mounted folders
# docker run --rm -v data:/data -v output:/output tcx-parser /data/myworkout.tcx --output /output/results.xlsx --mongo
# docker run --rm -v data:/data -v output:/output tcx-parser /data --output /output/results.xlsx --mongo

