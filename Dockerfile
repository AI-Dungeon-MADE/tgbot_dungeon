FROM python:3.9-slim-buster

COPY requirements.txt /requirements.txt
RUN pip install -r /requirements.txt --no-cache-dir --default-timeout=100
COPY . /app/

CMD python app/main.py