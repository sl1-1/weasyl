FROM debian:stretch

LABEL Description="Weasyl Dev Image"

RUN apt-get -y update
RUN apt-get -y dist-upgrade
RUN apt-get -y install \
    apt-transport-https ca-certificates curl \
    git-core libffi-dev libmagickcore-dev libpam-systemd libssl-dev \
    libxml2-dev libxslt-dev pkg-config liblzma-dev \
    python-dev python-virtualenv sassc build-essential python-pip

ADD https://www.postgresql.org/media/keys/ACCC4CF8.asc /etc/apt/trusted.gpg.d/apt.postgresql.org.asc

RUN echo >/etc/apt/sources.list.d/postgresql.list \
    'deb https://apt.postgresql.org/pub/repos/apt/ stretch-pgdg main 9.6'

RUN apt-get -y --allow-unauthenticated install \
    libpq-dev postgresql-9.6 postgresql-contrib-9.6

#ADD https://deb.nodesource.com/gpgkey/nodesource.gpg.key /etc/apt/trusted.gpg.d/deb.nodesource.com.asc
#
#RUN echo >/etc/apt/sources.list.d/nodesource.list \
#    'deb https://deb.nodesource.com/node_6.x stretch main'
#
#RUN apt-get -y --allow-unauthenticated install \
#    libpq-dev nodejs

#COPY etc/systemd/system/nginx.service.d/restart.conf /etc/systemd/system/nginx.service.d/
#
#RUN openssl req -subj '/CN=lo.weasyl.com' -nodes -new -newkey rsa:2048 \
#    -keyout /etc/ssl/private/weasyl.key.pem -out /tmp/weasyl.req.pem
#RUN openssl x509 -req -days 3650 -in /tmp/weasyl.req.pem \
#    -signkey /etc/ssl/private/weasyl.key.pem -out /etc/ssl/private/weasyl.crt.pem

#COPY etc/nginx/sites-available/weasyl /etc/nginx/sites-available/
#
#RUN ln -fs /etc/nginx/sites-available/weasyl /etc/nginx/sites-enabled

RUN  pip install -U pip setuptools
ADD etc/pip.conf /etc/
ADD etc/requirements.txt /etc/
RUN pip install -r /etc/requirements.txt


RUN pip install pytest==4.6.5 flake8

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

ENTRYPOINT pip install -Ue libweasyl && alembic upgrade head && twistd -ny weasyl/weasyl.tac
