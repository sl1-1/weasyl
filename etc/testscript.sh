#!/usr/bin/env sh


echo $WEASYL_TEST_SQLALCHEMY_URL
pip install -Ue libweasyl
pytest --cov=libweasyl libweasyl |tee /vagrant/testlogs/test.log
rm -rf /vagrant/testing
pytest --cov=weasyl --cov-append weasyl/test |tee -a /vagrant/testlogs/test.log
coverage html