# Solar Logger

## Info

This project is a multi-step program which relies on a MQTT backend to read information from an Outback solar controller which sends statistics of current battery status, input voltages etc. This program subscribes to the MQTT broker to retrieve the information broadcast and deciphers the raw byte streams into a readable form. It then converts the data into points to allow insertion into a time series database (InfluxDB) where the data can be stored, modeled and queried. The database will link to a Grafana website which will graph, model and compare the data on a privately accessible site.

## InfluxDB Setup

This project comes with a mostly pre-built Influx instance that you can run up or copy to a Docker server. All Influx configurations will be written to the folder `docker_influxdb`. If this is your first time running InfluxDB I would suggest uncommenting the following code in the `docker_compose.yml` and copying specified `.env` file into the base directory. 
```yml
InfluxDB:
    # For first time setup use these variables
    environment:
      - DOCKER_INFLUXDB_INIT_MODE=$influx_mode
      - DOCKER_INFLUXDB_INIT_USERNAME=$influx_username
      - DOCKER_INFLUXDB_INIT_PASSWORD=$influx_password
      - DOCKER_INFLUXDB_INIT_ORG=$influx_org
      - DOCKER_INFLUXDB_INIT_BUCKET=$influx_bucket
      - DOCKER_INFLUXDB_INIT_ADMIN_TOKEN=$influx_token
```
All following Docker restarts should keep their data.

## Solar Logger Setup

To start, fill out the `.env` template file with personal secrets and copy them to the base director. Then after running a Docker compose it will use the environmental variables to start the service and start writing data into Influx. If any errors occur then look through the Docker log files.

## Contents

### Logging

All programs below are implemented with a file logger which can be configured through the config.ini file, this can be used for program info or debugging purposes. If file logging is enabled all logs will be written in the `output` folder although if using within a Docker instance it will be written to `docker_output` instead.

**Note:** by default a `docker_output` volume is created. If you're not using file logging, comment out the following code in the `docker_compose.yml`:
```yml
SolarLogger:
    volumes:
      - ./docker_output:/app/output:rw
```

### Configurations

All debugging and querying options can be changed through the config file. If file logging is set to false then the generated output will be set by default to the debug console. There is also additional options for querying modes *(more detail in **influx_query.py**)*.

```ini
[influx_debugger]
file_logging    = True
; Only needed if file logging is true
file_location   = Output/
filename        = influx_logs.log
filemode        = a
format          = %%(asctime)s, %%(name)s, %%(levelname)s, %%(message)s
dateformat      = %%H:%%M:%%S
; Logging levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
debug_level     = DEBUG

[solar_debugger]
file_logging    = True
; Only needed if file logging is true
file_location   = Output/
filename        = solar_logs.log
filemode        = a
format          = %%(asctime)s, %%(name)s, %%(levelname)s, %%(message)s
dateformat      = %%H:%%M:%%S
;Logging levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
debug_level     = DEBUG

[query_settings]
; Can be either 'csv, 'flux' or 'stream'
query_mode      = flux
; Following three values are only required for CSV's
csv_location    = Output/
csv_name        = query_result.csv
csv_mode        = w
```

___

## Program Files

### Solar Logger

Defines the program that deals with subscribing to the solar controller's broker using MQTT, decodes the raw packets, and inputs the data points into a time series database *(Influx DB)*.

**Usage:** To use this program you must set up an Influx controller which connects to the Influx database and also set up a MQTT subscriber. The MQTT subscriber requires an Influx controller instance for it to run since it uses the controller to write data as it receives the data points.

Firstly create an Influx controller instance to manage and write to the Influx database.

```python
def create_influx_controller(influx_secret):
    """
    classes function that creates a InfluxController for use
    :param influx_secret: Secret passwords nad logins for Influx database
    :return: A database object which can be used to write/read data points
    """
    database = InfluxController(
        influx_secret.token,
        influx_secret.org,
        influx_secret.bucket,
        influx_secret.url
    )
    database.startup()
    return database
```

Afterwards create a MQTT listening service that runs indefinitely to retrieve data points from the solar broker, from which will then insert the data points into the Influx database.

```python
def mqtt_runtime(mqtt_secret, influx_database):
    """
    classes function that creates a MQTT client
    :param mqtt_secret: Secret passwords nad logins for MQTT subscriber
    :param influx_database: An Influx database object for the MQTTDecoder to write to
    :return: Never returns (see mq.mqtt_runtime())
    """
    mqtt = MQTTDecoder(
        mqtt_secret.host,
        mqtt_secret.port,
        mqtt_secret.user,
        mqtt_secret.password,
        mqtt_secret.topic,
        influx_database
    )
    mqtt.startup()
    mqtt.mqtt_runtime()
```

The MQTT runtime will call on the `MQTTDecoder` class from **mqtt_classes.py** which will listen and record data points.

`_on_connect()` runs when the MQTT subscriber firstly connects to the MQTT broker, in our case it uses the secrets file *(excluded passwords file)*  to choose what subscription to listen to.

`_on_message()` runs every time the MQTT subscriber receives a message from the broker.

### Influx Queries

Defines a program that generates and handles Influx queries using the Influx query api using the QueryBuilder class in **influx_classes.py**.

**Usage:** To use the Influx query program you must run the Python in an interactive instance:

`python -i .\influx_query.py`

Upon startup you will get the opportunity to create and modify queries. To start run `QueryBuilder.help()` for valid query commands. Then to generate a query string you create a QueryBuilder instance and add strings to your query like below:

You can currently apply the following fields to a query:

* `from(bucket:bucket_name)`, field for choosing the source bucket **(required)**.
* `range(start: -20m)`, field for choosing how long you want to poll the database **(required)**.
* `append_filter(field_1, value_1, joiner, new_band)`, takes the following parameters; field type, field value, joiner *('AND' or 'OR')*, new line boolean *(adds a newline to the filter)*.
* `append_aggregate(collection_window, aggregate_function)`, take the following parameters; how long to apply the aggregation over, type of aggregation function *(e.g. min/max)*.
* `append_sort(field, desc)`, takes the following parameters; field to sort by, show in descending order.

When running the query the program will take the query options from config.ini to decide what format to return the data in.
When querying the Influx database you can use three data types to assign the result to, those being the following:

* Raw CSV file
* Flux file *(returns a Python dictionary)*
* Stream file *(returns a FluxRecord object)*

*Currently, the program doesn't support parsing of stream files but will handle writing CSV files and printing Flux files.*

After building up a query you can submit the query by running `execute_query(query)`.