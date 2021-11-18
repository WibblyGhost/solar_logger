#syntax=docker/query.dockerfile:1
FROM python:3.9 AS build

RUN pip install --upgrade pip
RUN apt-get update

RUN mkdir "app"
WORKDIR "app"

ADD influx_query.py app/
ADD /classes/influx_classes.py app/classes/influx_classes.py
ADD /classes/py_functions.py app/classes/py_functions.py
ADD /private/ app/private/
ADD requirements.txt app/
ADD config.ini app/

RUN pip install -r app/requirements.txt

#INFLUX PORTS
EXPOSE 8086
EXPOSE 8088

CMD ["python", "app/influx_query.py"]