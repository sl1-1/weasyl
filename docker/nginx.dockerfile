FROM nginx:alpine

RUN apk update \
    && apk add openssl

RUN openssl req -subj '/CN=lo.weasyl.com' -nodes -new -newkey rsa:2048 \
    -keyout /etc/ssl/private/weasyl.key.pem -out /tmp/weasyl.req.pem
RUN openssl x509 -req -days 3650 -in /tmp/weasyl.req.pem \
    -signkey /etc/ssl/private/weasyl.key.pem -out /etc/ssl/private/weasyl.crt.pem

RUN mkdir /vagrant
RUN mkdir /vagrant/build
RUN mkdir /vagrant/static

EXPOSE 8443/TCP