FROM mcr.microsoft.com/devcontainers/python:1-3.10-bullseye

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
      build-essential \
      git \
      curl \
      unzip \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir --upgrade pip setuptools wheel
