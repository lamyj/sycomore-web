FROM debian:stretch

ADD ./sycomore/requirements.txt /tmp/requirements.txt

RUN \
  apt-get update && \
  apt-get install -y python3 python3-pip && \
  pip3 install -r /tmp/requirements.txt

ADD ./sycomore /opt/sycomore/
WORKDIR /opt/sycomore

CMD \
  bokeh serve \
    --address=0.0.0.0 --port=$PORT \
    --allow-websocket-origin=sycomore.herokuapp.com \
    --allow-websocket-origin=localhost:5006 \
    --use-xheaders \
    ./ 
