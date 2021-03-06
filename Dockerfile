FROM python:3.7.6-stretch

ADD . /tests

ARG TOKEN

RUN apt update && \
    apt upgrade -y && \
    apt install git && \
    git config --global url."https://$TOKEN:@github.com/".insteadOf "https://github.com/" && \
    pip3.7 install -r /tests/requirements.txt && \
    cp -r /usr/local/lib/python3.7/site-packages/revizor2/config /root/.revizor && \
    mkdir /root/.revizor/logs && \
    mkdir /root/.revizor/keys && \
    rm -rf /root/.cache/pip

ENV PYTHONPATH=/tests/

WORKDIR /tests
