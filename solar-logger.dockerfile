FROM python:3.10.2 as builder
ARG BASE_DIR="solarlogger"
WORKDIR ${BASE_DIR}
# Run updates
RUN apt-get update && pip install --upgrade pip
ADD requirements.txt ./
RUN pip install -r ./requirements.txt
# /config -> /solarlogger/config
ADD ./config/config.ini config/config.ini

FROM builder as solar-logger
ARG BASE_DIR
# /app -> /solarlogger/app
ADD ./app/solar_main.py app/solar_main.py
# /classes -> /solarlogger/classes
ADD ./classes/common_classes.py classes/common_classes.py
ADD ./classes/consts.py classes/consts.py
ADD ./classes/custom_exceptions.py classes/custom_exceptions.py
ADD ./classes/influx_classes.py classes/influx_classes.py
ADD ./classes/mqtt_classes.py classes/mqtt_classes.py
ADD ./classes/py_functions.py classes/py_functions.py
ADD ./classes/py_logger.py classes/py_logger.py
# Run instance
CMD [ "python", "app/solar_main.py" ]

FROM builder as influx-query
ARG BASE_DIR
# Add required modules
# /app -> /solarlogger/app
ADD ./app/influx_query.py app/influx_query.py
# /classes -> /solarlogger/classes
ADD ./classes/common_classes.py classes/common_classes.py
ADD ./classes/consts.py classes/consts.py
ADD ./classes/custom_exceptions.py classes/custom_exceptions.py
ADD ./classes/influx_classes.py classes/influx_classes.py
ADD ./classes/py_functions.py classes/py_functions.py
ADD ./classes/py_logger.py classes/py_logger.py
ADD ./classes/query_classes.py classes/query_classes.py
# Run instance
CMD [ "python", "-i", "app/influx_query.py"]

FROM python:3.10.2 as unit-tests
ARG BASE_DIR="solar_logger"
WORKDIR /solarlogger/
# Run updates
RUN apt-get update && pip install --upgrade pip
ADD requirements.txt ./requirements.txt
ADD requirements-test.txt ./requirements-test.txt
RUN pip install -r requirements-test.txt
ADD ./app/ app/
ADD ./classes/ classes/
ADD ./tests/ tests/
# Run instance
CMD [ "python", "-m", "pytest", "./tests"]
