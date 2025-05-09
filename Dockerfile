FROM python:3.12-slim-bullseye
RUN apt-get update && apt-get install -y supervisor
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf
CMD ["supervisord", "-n"]
