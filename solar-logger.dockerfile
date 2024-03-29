FROM python:3.10.2 as builder
ARG BASE_DIR="solarlogger"
WORKDIR ${BASE_DIR}
# Run updates
RUN apt-get update && pip install --upgrade pip
ADD requirements.txt requirements.txt
RUN pip install -r requirements.txt
# /config -> /solarlogger/config
ADD src/config/config.ini src/config/config.ini

FROM builder as solar-logger
ARG BASE_DIR
ADD start_logger.py start_logger.py
# /app -> /solarlogger/app
ADD src/app/solar_main.py src/app/solar_main.py
# /classes -> /solarlogger/classes
ADD src/classes/common_classes.py src/classes/common_classes.py
ADD src/classes/custom_exceptions.py src/classes/custom_exceptions.py
ADD src/classes/influx_classes.py src/classes/influx_classes.py
ADD src/classes/mqtt_classes.py src/classes/mqtt_classes.py
# /helpers -> /solarlogger/helpers
ADD src/helpers/consts.py src/helpers/consts.py
ADD src/helpers/py_functions.py src/helpers/py_functions.py
ADD src/helpers/py_logger.py src/helpers/py_logger.py
# Run instance
CMD [ "python", "start_logger.py" ]

FROM builder as influx-query
ARG BASE_DIR
# Add required modules
ADD start_query.py start_query.py
# /app -> /solarlogger/app
ADD src/app/influx_query.py src/app/influx_query.py
# /classes -> /solarlogger/classes
ADD src/classes/common_classes.py src/classes/common_classes.py
ADD src/classes/custom_exceptions.py src/classes/custom_exceptions.py
ADD src/classes/influx_classes.py src/classes/influx_classes.py
ADD src/classes/query_classes.py src/classes/query_classes.py
# /helpers -> /solarlogger/helpers
ADD src/helpers/consts.py src/helpers/consts.py
ADD src/helpers/py_functions.py src/helpers/py_functions.py
ADD src/helpers/py_logger.py src/helpers/py_logger.py
# Run instance
CMD [ "python", "-i", "start_query.py"]

FROM python:3.10.2 as unit-tests
ARG BASE_DIR="solar_logger"
WORKDIR /solarlogger/
# Run updates
RUN apt-get update && pip install --upgrade pip
ADD requirements.txt requirements.txt
ADD requirements-test.txt requirements-test.txt
RUN pip install -r requirements-test.txt
ADD src/ src/
ADD tests/ tests/
ADD pyproject.toml pyproject.toml
# Run instance
CMD [ "python", "-m", "pytest"]
