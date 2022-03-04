FROM python:3.9

RUN pip install --upgrade pip
RUN apt-get update

ADD influx_query.py app/
ADD solar_runtime.py app/
ADD /classes/ app/classes/
ADD /private/ app/private/
ADD /config/ app/config/

ADD requirements.txt app/
RUN pip install -r app/requirements.txt

WORKDIR "/app"

#INFLUX PORTS
EXPOSE 8086
EXPOSE 8088

CMD ["python", "influx_query.py"]