FROM python:3.11-alpine

RUN apk add build-base && \
    pip install faust-cchardet

RUN apk add bash

COPY . /opt/pimht
WORKDIR /opt/pimht
ENV PYTHONPATH .
