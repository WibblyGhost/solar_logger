#syntax=docker/solar.dockerfile:1
FROM python:3.9 AS build

RUN pip install --upgrade pip
RUN apt-get update

RUN mkdir "app"
WORKDIR "app"

ADD solar_runtime.py app/
ADD /classes/ app/classes/
ADD /private/ app/private/
ADD requirements.txt app/
ADD config.ini app/

RUN pip install -r app/requirements.txt

#INFLUX PORTS
EXPOSE 8086
EXPOSE 8088

#MQTT PORTS
EXPOSE 8883

CMD ["python", "app/solar_runtime.py"]