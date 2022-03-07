FROM python:3.10.2

WORKDIR /app/

# Run updates
RUN apt-get update && pip install --upgrade pip
ADD requirements.txt /app/
RUN pip install -r /app/requirements.txt

# Add required modules
ADD postgresql_connector.py /app/
ADD /config/ /app/config/
# ADD /classes/py_functions.py /app/classes/py_functions.py

# Setting environment variables
ENV INFLUX_URL = "$INFLUX_URL"
ENV INFLUX_ORG = "$INFLUX_ORG"
ENV INFLUX_BUCKET = "$INFLUX_BUCKET"
ENV INFLUX_TOKEN = "$INFLUX_TOKEN"

# Run instance
CMD ["python", "postgresql_connector.py"]
