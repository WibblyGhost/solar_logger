FROM python:3.10.2

RUN apt-get update && pip install --upgrade pip

# Docker permissions lockdown
RUN adduser -disabled-password myuser
USER myuser
WORKDIR /home/myuser/app
COPY --chown=myuser:myuser requirements.txt requirements.txt
RUN pip install --user -r requirements.txt
ENV PATH="/home/user/.local/bin:${PATH}"

# Add needed modules
ADD solar_runtime.py /home/myuser/app/
ADD /config/ /home/myuser/app/config/
ADD /classes/mqtt_classes.py /home/myuser/app/classes/mqtt_classes.py
ADD /classes/influx_classes.py /home/myuser/app/classes/influx_classes.py
ADD /classes/py_functions.py /home/myuser/app/classes/py_functions.py

# Setup environment variables
ENV INFLUX_URL = "$INFLUX_URL"
ENV INFLUX_ORG = "$INFLUX_ORG"
ENV INFLUX_BUCKET = "$INFLUX_BUCKET"
ENV INFLUX_TOKEN = "$INFLUX_TOKEN"

ENV MQTT_HOST = "$MQTT_HOST"
ENV MQTT_PORT = "$MQTT_PORT"
ENV MQTT_USER = "$MQTT_USER"
ENV MQTT_TOKEN = "$MQTT_TOKEN"
ENV MQTT_TOPIC = "$MQTT_TOPIC"

# Run instance
CMD [ "python", "solar_runtime.py" ]