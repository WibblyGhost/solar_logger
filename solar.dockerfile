FROM python:3.10.2

RUN apt-get update
RUN pip install --upgrade pip

ADD solar_runtime.py /app/
ADD /classes/ /app/classes/
ADD /config/ /app/config/
ADD /classes/solar_classes.py /app/classes/solar_classes.py
ADD /classes/py_functions.py /app/classes/py_functions.py

ADD requirements.txt /app/
RUN pip install -r /app/requirements.txt

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