FROM python:3.10.2

WORKDIR /app/

# Run updates
RUN apt-get update && pip install --upgrade pip
ADD requirements.txt /app/
RUN pip install -r /app/requirements.txt

# Add required modules
ADD influx_query.py /app/
# /config -> /app/config
ADD /config/ /app/config/
# /classes -> /app/classes
ADD /classes/common_classes.py /app/classes/common_classes.py
ADD /classes/consts.py /app/classes/consts.py
ADD /classes/custom_exceptions.py /app/classes/custom_exceptions.py
ADD /classes/influx_classes.py /app/classes/influx_classes.py
ADD /classes/py_functions.py /app/classes/py_functions.py
ADD /classes/py_logger.py /app/classes/py_logger.py
ADD /classes/query_classes.py /app/classes/query_classes.py

# Run instance
CMD [ "python", "-i", "./influx_query.py"]
