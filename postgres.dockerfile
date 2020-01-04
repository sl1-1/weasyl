FROM postgres:9.6


ADD https://deploy.weasyldev.com/weasyl-latest-staff.sql.xz /tmp/weasyl-latest-staff.sql.xz
RUN echo 'CREATE EXTENSION hstore;' > /docker-entrypoint-initdb.d/init.sql
RUN xzcat /tmp/weasyl-latest-staff.sql.xz | sed '/^CREATE OPERATOR FAMILY .*/d' >> /docker-entrypoint-initdb.d/init.sql


EXPOSE 5432/tcp


