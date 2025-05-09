FROM python:3.12-slim-bullseye
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
RUN chmod +x ./start.sh
CMD ["./start.sh"]
