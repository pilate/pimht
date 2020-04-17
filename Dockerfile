FROM python:3.8-alpine3.10

RUN apk add build-base && \
    pip install cchardet

RUN apk add bash

COPY . /opt/pimht
WORKDIR /opt/pimht
ENV PYTHONPATH .
