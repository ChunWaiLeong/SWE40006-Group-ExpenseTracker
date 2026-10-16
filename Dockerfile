FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .
COPY migrations ./migrations
COPY templates ./templates

ENV APP_ENV=production
ENV PORT=5000

EXPOSE 5000

CMD ["sh", "-c", "gunicorn --workers 2 --bind 0.0.0.0:${PORT:-5000} app:app"]