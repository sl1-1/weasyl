FROM node:alpine

LABEL Description="Weasyl Nodebuild Image"

RUN apk add sassc

RUN mkdir /vagrant

WORKDIR /vagrant

ADD package-lock.json /vagrant
ADD package.json /vagrant

ADD build.js /vagrant

RUN npm install

ENTRYPOINT cd /vagrant && node build.js