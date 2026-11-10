FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/data

EXPOSE 3010

CMD ["gunicorn", "--bind", "0.0.0.0:3010", "--workers", "2", "--threads", "4", "app:app"]
