FROM weasyl_base:latest

LABEL Description="Weasyl Dev Image"

RUN pip install pytest flake8 coverage pytest-cov pytest-profiling==1.6.0

EXPOSE 8443/tcp

WORKDIR /vagrant

ENTRYPOINT /testscript.sh