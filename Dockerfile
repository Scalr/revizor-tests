FROM python:3.6.8-stretch

ADD . /tests

ARG TOKEN

RUN apt update && \
    apt install git && \
    git config --global url."https://$TOKEN:@github.com/".insteadOf "https://github.com/" && \
    pip install -r /tests/requirements.txt

WORKDIR /tests
