# Dockerfile
FROM python:3.11-slim

# (Optional) system deps some libs expect; harmless + tiny
RUN apt-get update && apt-get install -y build-essential && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

ENV PORT=8000
EXPOSE 8000

# If your app folder is named differently, adjust the module path below.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
