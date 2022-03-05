FROM python:3.10.2

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

CMD ["python", "-i influx_query.py"]