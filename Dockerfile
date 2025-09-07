FROM python:3.12-alpine

RUN apk add build-base && \
    pip install faust-cchardet pybase64

RUN apk add bash

COPY . /opt/pimht
WORKDIR /opt/pimht
ENV PYTHONPATH .
