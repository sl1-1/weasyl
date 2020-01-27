FROM alpine:latest

LABEL Description="Weasyl Base Image"

RUN echo "@testing http://dl-cdn.alpinelinux.org/alpine/edge/main" >> /etc/apk/repositories

RUN apk update && \
    apk add postgresql-client postgresql-dev \
    gcc g++ make \
    python2 python2-dev py2-pip \
    py2-pillow@testing\
    cython \
    imagemagick6 imagemagick6-dev libffi libffi-dev \
    zlib zlib-dev libxml2 libxml2-dev libxslt libxslt-dev \
    xz xz-dev jpeg-dev libwebp libwebp-dev git

RUN  pip install -U pip setuptools wheel
ADD ./etc/pip.conf /etc/
ADD ./etc/_requirements.txt /etc/requirements.txt

RUN pip install -r /etc/requirements.txt
RUN pip install jinja2 lxml psycopg2cffi sanpera misaka alembic

RUN mkdir /vagrant
RUN mkdir /vagrant/weasyl
RUN mkdir /vagrant/libweasyl
RUN mkdir /vagrant/build

ADD ./libweasyl/libweasyl/alembic/alembic.ini.example /vagrant/alembic.ini

RUN mkdir /vagrant/config
ADD ./config/site.config.txt.example /vagrant/config/site.config.txt
ADD ./config/weasyl-staff.example.py /vagrant/config/weasyl-staff.py


WORKDIR /vagrant