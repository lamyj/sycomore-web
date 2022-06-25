FROM python:3.9.13

ADD ./sycomore/requirements.txt /tmp/requirements.txt

RUN pip3 install -r /tmp/requirements.txt

ADD ./sycomore /opt/sycomore/
WORKDIR /opt/sycomore

CMD \
  bokeh serve \
    --address=0.0.0.0 --port=$PORT \
    --allow-websocket-origin=sycomore.herokuapp.com \
    --allow-websocket-origin=localhost:${PORT} \
    --use-xheaders \
    ./ 
