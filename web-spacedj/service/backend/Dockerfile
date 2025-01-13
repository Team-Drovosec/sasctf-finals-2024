FROM ubuntu:22.04

WORKDIR /tmp

ENV DEBIAN_FRONTEND="noninteractive" TZ="Europe/London"
RUN apt update && apt install -y python3 python3-pip libavcodec58 libavfilter7 libavformat58
RUN apt install -y software-properties-common redis

RUN add-apt-repository ppa:deadsnakes/ppa
RUN apt install -y python3.12-full curl
RUN curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
RUN python3.12 get-pip.py

WORKDIR /app
COPY requirements.txt .
RUN python3.12 -m pip install -r requirements.txt

COPY app /app

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
CMD ["/entrypoint.sh"]