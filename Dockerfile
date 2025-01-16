FROM python:3.12.8

WORKDIR /app

ENV PYTHONUNBUFFERED=1

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY ./src ./src
COPY ./install_netcat.sh ./

EXPOSE 22

CMD [ "python", "./src/main.py" ]
