FROM mcr.microsoft.com/devcontainers/python:3.11

# Install dev tools
RUN apt-get update && apt-get install -y iputils-ping netcat-openbsd

# Optional: preinstall pip dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt