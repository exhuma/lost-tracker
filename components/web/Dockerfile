FROM python:2.7
WORKDIR /opt/app
RUN apt-get update
RUN mkdir /opt/app -p
RUN pip install flask gunicorn
COPY requirements.txt /opt/app
RUN pip install -r /opt/app/requirements.txt
COPY . /opt/app
RUN pip install /opt/app
VOLUME /var/lost_tracker/data
RUN mkdir -p /opt/app/.mamerwiselen/lost-tracker
COPY lost_tracker_docker.ini /opt/app/.mamerwiselen/lost-tracker/app.ini
COPY logging.conf /opt/app
CMD ["gunicorn", "--log-config", "logging.conf", "-w", "2", "-b", ":8000", "lost_tracker.main:make_app()"]
