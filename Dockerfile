FROM python:3.11-slim AS build

# RUN apt-get update
RUN apt-get update && apt-get install -y gcc python3-dev 
RUN pip install --upgrade pip

COPY . /app
WORKDIR /app

RUN pip install -e .

WORKDIR /app/data-gpt/


WORKDIR /app

