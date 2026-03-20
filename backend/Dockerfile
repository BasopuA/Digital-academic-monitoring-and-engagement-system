#Use the official python 3.11 image as base image
FROM python:3.11

# Upgrade pip first to avoid compatibility issues
RUN pip install --upgrade pip

#Installing curl using apt-get, for health checks 
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

#Set working directory to /app
WORKDIR /app

#Copy the requirements.txt file from current directory into container at /app
COPY requirements.txt .

#Install needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

#Copy all files and directories from host's current directory into /app
COPY . .

#Run app when the container launches
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]