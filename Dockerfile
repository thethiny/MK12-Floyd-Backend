FROM python:3.9-buster

WORKDIR /tmp
COPY requirements.txt .

RUN pip install -r requirements.txt --no-cache-dir

WORKDIR /app
COPY src src
COPY app.py .

CMD ["gunicorn", "-k", "gevent", "-w", "1", "--worker-connections", "500", "--preload", "-b", "0.0.0.0:8000", "app:app"]
