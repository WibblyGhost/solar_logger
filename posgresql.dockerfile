FROM python:3.10.2

ADD requirements.txt app/

RUN apt-get update
RUN pip install --upgrade pip
RUN pip install -r app/requirements.txt

# ADD solar_runtime.py app/
# ADD /classes/ app/classes/
# ADD /private/ app/private/
# ADD /config/ app/config/


WORKDIR "/app"

CMD ["python", "postgresql_connector.py"]