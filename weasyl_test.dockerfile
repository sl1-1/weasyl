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

RUN pip install -U pip setuptools
ADD etc/pip.conf /etc/
ADD etc/requirements.txt /etc/
RUN pip install -r /etc/requirements.txt
RUN pip install pytest==4.6.5 flake8

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

ENTRYPOINT pip install -Ue libweasyl && py.test weasyl/test
