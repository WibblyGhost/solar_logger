FROM python:3.10.2

ADD requirements.txt /app/

RUN apt-get update
RUN pip install --upgrade pip
RUN pip install -r /app/requirements.txt

ADD influx_query.py /app/
ADD /config/ /app/config/
ADD /classes/influx_classes.py /app/classes/influx_classes.py
ADD /classes/py_functions.py /app/classes/py_functions.py

ENV INFLUX_URL = "$INFLUX_URL"
ENV INFLUX_ORG = "$INFLUX_ORG"
ENV INFLUX_BUCKET = "$INFLUX_BUCKET"
ENV INFLUX_TOKEN = "$INFLUX_TOKEN"

WORKDIR "/app"

CMD [ "python", "-i", "./influx_query.py"]
