FROM python:3.10.2

WORKDIR /app/

# Run updates
RUN apt-get update && pip install --upgrade pip
ADD requirements.txt /app/
RUN pip install -r /app/requirements.txt

# Add required modules
ADD influx_query.py /app/
ADD /config/ /app/config/
ADD /classes/custom_exceptions.py /app/classes/custom_exceptions.py
ADD /classes/influx_classes.py /app/classes/influx_classes.py
ADD /classes/py_functions.py /app/classes/py_functions.py
ADD /classes/py_logger.py /app/classes/py_logger.py
ADD /classes/query_classes.py /app/classes/query_classes.py

# Setting environment variables
ENV INFLUX_URL = "$INFLUX_URL"
ENV INFLUX_ORG = "$INFLUX_ORG"
ENV INFLUX_BUCKET = "$INFLUX_BUCKET"
ENV INFLUX_TOKEN = "$INFLUX_TOKEN"

# Run instance
CMD [ "python", "-i", "./influx_query.py"]
