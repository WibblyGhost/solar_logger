FROM python:3.9

RUN apt-get update
RUN pip install --upgrade pip

ADD solar_runtime.py app/
ADD /classes/ app/classes/
ADD /private/ app/private/
ADD /config/ app/config/
ADD /classes/solar_classes.py app/classes/solar_classes.py
ADD /classes/py_functions.py app/classes/py_functions.py

ADD requirements.txt app/
RUN pip install -r requirements.txt

WORKDIR "/app"

CMD [ "python", "solar_runtime.py" ]