FROM python:2.7
RUN apt-get update
RUN mkdir /opt/app -p
RUN pip install flask gunicorn
COPY . /opt/app
RUN pip install -r /opt/app/requirements.txt
CMD ["gunicorn", "-w", "2", "-b", ":8000", "app:app"]
