FROM python:3.12.8

WORKDIR /app

ENV PYTHONUNBUFFERED=1

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

RUN apt-get update && apt-get install -y netcat-openbsd nginx

COPY ./src ./src
COPY ./nginx/nginx_default_config /etc/nginx/sites-available/default
COPY ./nginx/nginx.conf /etc/nginx/nginx.conf
COPY ./start.sh ./start.sh

EXPOSE 22

CMD [ "/usr/bin/bash", "start.sh" ]
