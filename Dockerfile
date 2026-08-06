FROM python:3.12-slim

WORKDIR /app
COPY requirements-base.txt .
RUN pip install --no-cache-dir -r requirements-base.txt
COPY . .

EXPOSE 8000
CMD gunicorn statfort.wsgi --log-file - --bind 0.0.0.0:$PORT