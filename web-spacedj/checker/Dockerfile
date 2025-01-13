# FROM python:3.11
FROM ubuntu:22.04

WORKDIR /tmp

ENV DEBIAN_FRONTEND="noninteractive" TZ="Europe/London"
RUN apt update && apt install -y python3 python3-pip libavcodec58 libavfilter7 libavformat58
RUN apt install -y software-properties-common ffmpeg

RUN apt-get update &&\
    apt-get install -y gcc libpq-dev make build-essential libssl-dev zlib1g-dev \
  libbz2-dev libreadline-dev libsqlite3-dev wget curl llvm \
  libncursesw5-dev xz-utils tk-dev libxml2-dev libxmlsec1-dev libffi-dev liblzma-dev


RUN add-apt-repository ppa:deadsnakes/ppa
RUN apt install -y python3.12-full curl
RUN curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
RUN python3.12 get-pip.py


ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=${PYTHONPATH}:/app

RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libpq-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN pip install setuptools

RUN pip install setuptools --upgrade

COPY requirements.txt /requirements.txt
RUN pip install -r /requirements.txt


RUN mkdir /kek
COPY . /kek

# use docker run /kek/checker.py check 192.168.1.24
