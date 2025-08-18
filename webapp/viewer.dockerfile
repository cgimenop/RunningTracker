FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# For quicker reloads during development
# TODO: move to a separate Dockerfile for production
RUN pip install --no-cache-dir watchdog

COPY . /app

ARG FLASK_ENV=production
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_ENV=${FLASK_ENV}

EXPOSE 5000

CMD ["flask", "run"]