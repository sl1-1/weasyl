FROM weasyl_base:latest

LABEL Description="Weasyl Dev Image"

EXPOSE 8443/tcp

WORKDIR /vagrant

ENTRYPOINT pip install -Ue libweasyl && alembic upgrade head && twistd -ny weasyl/weasyl.tac