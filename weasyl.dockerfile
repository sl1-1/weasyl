FROM alpine:latest

LABEL Description="Weasyl Dev Image"

RUN apk update && \
    apk add postgresql-client postgresql-dev \
    gcc g++ make \
    python3 python3-dev \
    py3-pillow==6.2.1-r0 py3-lxml==4.4.2-r0 py3-twisted==19.10.0-r0 \
    py3-cryptography==2.8-r1 py3-bcrypt==3.1.7-r2 cython \
    imagemagick6 imagemagick6-dev libffi libffi-dev \
    zlib zlib-dev libxml2 libxml2-dev libxslt libxslt-dev \
    xz xz-dev jpeg-dev libwebp libwebp-dev git

RUN  pip3 install -U pip setuptools wheel
ADD etc/pip.conf /etc/
ADD etc/requirements.txt /etc/

RUN mkdir /pytemp
WORKDIR /pytemp
ADD ./sanpera /pytemp/sanpera
ADD ./misaka /pytemp/misaka
RUN pip3 install /pytemp/sanpera
RUN pip3 install -v /pytemp/misaka
RUN pip3 install -r /etc/requirements.txt


EXPOSE 8443/tcp

RUN mkdir /vagrant
RUN mkdir /vagrant/weasyl
RUN mkdir /vagrant/libweasyl
RUN mkdir /vagrant/build

ADD libweasyl/libweasyl/alembic/alembic.ini.example /vagrant/alembic.ini
RUN sed -i 's/\/weasyl/weasyl:example@postgres:5432\/weasyl/g' /vagrant/alembic.ini

RUN mkdir /vagrant/config
ADD config/site.config.txt.example /vagrant/config/site.config.txt
RUN sed -i 's/\/weasyl/weasyl:example@postgres:5432\/weasyl/g' /vagrant/config/site.config.txt
ADD config/weasyl-staff.example.py /vagrant/config/weasyl-staff.py


WORKDIR /vagrant

ENTRYPOINT pip3 install -Ue libweasyl && alembic upgrade head && twistd -ny weasyl/weasyl.tac
