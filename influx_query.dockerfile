FROM python:3.10.2

WORKDIR /app/

# Run updates
RUN apt-get update && pip install --upgrade pip
ADD requirements.txt /app/
RUN pip install -r /app/requirements.txt

# Add required modules
ADD /app/influx_query.py /app/
ADD /app/config/ /app/config/
ADD /app/classes/custom_exceptions.py /app/classes/custom_exceptions.py
ADD /app/classes/influx_classes.py /app/classes/influx_classes.py
ADD /app/classes/py_functions.py /app/classes/py_functions.py
ADD /app/classes/py_logger.py /app/classes/py_logger.py

# Setting environment variables
ENV INFLUX_URL = "$INFLUX_URL"
ENV INFLUX_ORG = "$INFLUX_ORG"
ENV INFLUX_BUCKET = "$INFLUX_BUCKET"
ENV INFLUX_TOKEN = "$INFLUX_TOKEN"

# Run instance
CMD [ "python", "-i", "./influx_query.py"]
