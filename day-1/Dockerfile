FROM python:3.12-slim
WORKDIR /lab
RUN pip install --no-cache-dir prometheus-client==0.22.1
COPY service.py traffic.py ./
