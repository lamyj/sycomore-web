FROM debian:buster

ADD ./sycomore/requirements.txt /tmp/requirements.txt
ADD ./sycomore /opt/sycomore/

RUN \
  apt-get update && \
  apt-get install -y python3 python3-pip && \
  pip3 install -r /tmp/requirements.txt

WORKDIR /opt/sycomore

CMD bokeh serve --port=$PORT ./ 
