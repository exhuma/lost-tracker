FROM ubuntu:xenial
RUN apt-get update
RUN apt-get install -y apache2 libapache2-mod-wsgi \
    libpq-dev libffi-dev python3-dev libjpeg-dev \
    build-essential python3-pip
RUN apt-get install -y git
RUN pip3 install -U pip
RUN pip install alembic gunicorn

ENV PIP_INDEX_URL=http://192.168.1.2:50000/root/pypi
ENV PIP_TRUSTED_HOST=192.168.1.2

ENV TRACKER_DSN=postgresql://lost@database/lost
ENV TRACKER_HELPDESK=
ENV TRACKER_PHOTO_FOLDER=/data/photos
ENV TRACKER_HTTP_LOGIN=http_login
ENV TRACKER_HTTP_PASSWORD=http_passwd
ENV TRACKER_SECRET_KEY=unsecure
ENV TRACKER_SHOUT=
ENV TRACKER_FLICKR_API_KEY=

COPY dist-requirements.txt /
COPY dist/docker.tar.gz /
COPY entry-point.bash /
RUN mkdir -p /alembic
ADD alembic /alembic/alembic
ADD alembic.ini /alembic
RUN pip install alembic
RUN chmod +x /entry-point.bash
RUN pip install -r /dist-requirements.txt
RUN pip install /docker.tar.gz
RUN mkdir -p /etc/mamerwiselen/lost-tracker
COPY app.ini.dist /
COPY materialize_config.py /
EXPOSE 8080
ENTRYPOINT ["/entry-point.bash"]
