FROM python:3.10.12

ENV PYTHONUNBUFFERED 1

RUN apt-get -y update
RUN apt-get -y install vim

RUN mkdir /app
ADD . /app
WORKDIR /app

RUN pip install --upgrade pip
RUN pip install -r requirements.txt
COPY .env .

COPY requirements-prod.txt .
RUN pip install --no-cache-dir -r requirements-prod.txt