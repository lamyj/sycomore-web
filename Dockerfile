FROM heroku/miniconda

ADD ./sycomore-web/requirements.txt /tmp/requirements.txt
ADD ./sycomore-web /opt/sycomore-web/

RUN pip install -qr /tmp/requirements.txt
RUN conda install -c conda-forge sycomore

WORKDIR /opt/sycomore-web

CMD voila --port=$PORT --no-browser app.ipynb
