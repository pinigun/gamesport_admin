FROM python:3.12-slim-bullseye
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
CMD python3 -m campaign_scheduler.main && gunicorn app:app --workers 6 --bind 0.0.0.0:8015 --max-requests 1000 --timeout 30 --graceful-timeout 30 --keep-alive 75 --worker-class uvicorn.workers.UvicornWorker

