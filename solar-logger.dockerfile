FROM python:3.10.2 as builder
# Run updates
WORKDIR /app/
RUN apt-get update && pip install --upgrade pip
ADD requirements.txt ./
RUN pip install -r ./requirements.txt
# Add required modules
# /config -> /app/config
ADD ./solar-logger/config/config.ini ./config/config.ini

FROM builder as solar-logger
# Add required modules
ADD ./solar-logger/solar_logger.py ./solar_logger.py
# /classes -> /app/classes
ADD ./solar-logger/classes/common_classes.py ./classes/common_classes.py
ADD ./solar-logger/classes/consts.py ./classes/consts.py
ADD ./solar-logger/classes/custom_exceptions.py ./classes/custom_exceptions.py
ADD ./solar-logger/classes/influx_classes.py ./classes/influx_classes.py
ADD ./solar-logger/classes/mqtt_classes.py ./classes/mqtt_classes.py
ADD ./solar-logger/classes/py_functions.py ./classes/py_functions.py
ADD ./solar-logger/classes/py_logger.py ./classes/py_logger.py
# Run instance
CMD [ "python", "solar_logger.py" ]

FROM builder as influx-query
# Add required modules
ADD ./solar-logger/influx_query.py ./influx_query.py
# /classes -> /app/classes
ADD ./solar-logger/classes/common_classes.py ./classes/common_classes.py
ADD ./solar-logger/classes/consts.py ./classes/consts.py
ADD ./solar-logger/classes/custom_exceptions.py ./classes/custom_exceptions.py
ADD ./solar-logger/classes/influx_classes.py ./classes/influx_classes.py
ADD ./solar-logger/classes/py_functions.py ./classes/py_functions.py
ADD ./solar-logger/classes/py_logger.py ./classes/py_logger.py
ADD ./solar-logger/classes/query_classes.py ./classes/query_classes.py
# Run instance
CMD [ "python", "-i", "./influx_query.py"]
