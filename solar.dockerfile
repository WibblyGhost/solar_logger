FROM python:3.10.2

ADD requirements.txt /app/

RUN apt-get update
RUN pip install --upgrade pip
RUN pip install -r /app/requirements.txt

ADD solar_runtime.py /app/
ADD /config/ /app/config/
ADD /classes/mqtt_classes.py /app/classes/mqtt_classes.py
ADD /classes/influx_classes.py /app/classes/influx_classes.py
ADD /classes/py_functions.py /app/classes/py_functions.py

ENV INFLUX_URL = "$INFLUX_URL"
ENV INFLUX_ORG = "$INFLUX_ORG"
ENV INFLUX_BUCKET = "$INFLUX_BUCKET"
ENV INFLUX_TOKEN = "$INFLUX_TOKEN"

ENV MQTT_HOST = "$MQTT_HOST"
ENV MQTT_PORT = "$MQTT_PORT"
ENV MQTT_USER = "$MQTT_USER"
ENV MQTT_TOKEN = "$MQTT_TOKEN"
ENV MQTT_TOPIC = "$MQTT_TOPIC"

WORKDIR "/app"

CMD [ "python", "solar_runtime.py" ]