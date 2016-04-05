FROM python:2.7
RUN apt-get update
RUN mkdir /opt/app -p
RUN pip install flask gunicorn
COPY app.py /opt/app
