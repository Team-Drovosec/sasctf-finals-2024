FROM ubuntu:22.04

RUN apt-get update &&\
    apt-get install -y gcc curl unzip

# THE VERSION IS ***IMPORTANT***
RUN curl -fsSL https://bun.sh/install | bash -s "bun-v1.1.26"
WORKDIR /checkers/mine/
RUN export BUN_INSTALL="$HOME/.bun"
RUN export PATH=$BUN_INSTALL/bin:$PATH

COPY . .
COPY check.sh /

RUN chmod +x install.sh
RUN ./install.sh

# use docker run /check.sh check 192.168.1.24
