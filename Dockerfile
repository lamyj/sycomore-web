FROM debian:buster

ADD ./sycomore-web/requirements.txt /tmp/requirements.txt
ADD ./sycomore-web /opt/sycomore-web/

RUN \
  apt-get update && \
  apt-get install -y python3 python3-pip && \
  pip3 install -U pip && \
  /usr/local/bin/pip3 install -r /tmp/requirements.txt

WORKDIR /opt/sycomore-web

CMD voila --port=$PORT --no-browser app.ipynb
