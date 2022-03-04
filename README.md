# Solar-Logger

This project is a multi-step program which relies on a MQTT backend to read information from an Outback solar controller which sends statistics of current battery status, input voltages etc. This program subscribes to the MQTT broker to retrieve the information broadcast and deciphers the raw byte streams into a readable form. It then converts the data into points to allow insertion into a time series database (InfluxDB) where the data can be stored, modeled and queried. The database will link to a Grafana website which will graph, model and compare the data on a privately accessible site.

___

### Logging

All programs below are implemented with a file logger which can be configured through the config.ini file, this can be used for program info or debugging purposes.
___

### config.ini

All debugging and querying options can be changed through the config file. If file logging is set to false then the generated output will be set by default to the debug console. There is also additional options for querying modes *(more detail in **influx_query.py**)*.

```ini
[influx_debugger]
file_logging    = True
; Only needed if file logging is true
file_location   = ../Output/
filename        = influx_logs.log
filemode        = a
format          = %%(asctime)s, %%(name)s, %%(levelname)s, %%(message)s
dateformat      = %%H:%%M:%%S
; Logging levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
debug_level     = DEBUG

[solar_debugger]
file_logging    = True
; Only needed if file logging is true
file_location   = ../Output/
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
csv_location    = ../Output/
csv_name        = query_result.csv
csv_mode        = w
```

## Program Files

___

### solar_runtime.py

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
    database = InfluxController(influx_secret.token,
                                influx_secret.org,
                                influx_secret.bucket,
                                influx_secret.url)
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
    mq = MQTTDecoder(mqtt_secret.host,
                     mqtt_secret.port,
                     mqtt_secret.user,
                     mqtt_secret.password,
                     mqtt_secret.topic,
                     influx_database)
    mq.startup()
    mq.mqtt_runtime()
```

The MQTT runtime will call on the `MQTTDecoder` class from **solar_classes.py** which will listen and record data points.

`_on_connect()` runs when the MQTT subscriber firstly connects to the MQTT broker, in our case it uses the secrets file *(excluded passwords file)*  to choose what subscription to listen to.

`_on_message()` runs everytime the MQTT subscriber receives a message from the broker.

___

### influx_query.py

Defines a program that generates and handles Influx queries using the Influx query api using the QueryBuilder class in **influx_classes.py**.

**Usage:** To use the query builder you must fist create an Influx query instance through, *InfluxController*.

```python
def create_influx_controller(influx_secret) -> InfluxController:
    """
    :param influx_secret: Class of secrets to connect to the Influx database
    :return: InfluxController instance to run queries on
    """
    database = InfluxController(influx_secret.token,
                                influx_secret.org,
                                influx_secret.bucket,
                                influx_secret.url)
    database.startup()
    return database
```

Then to generate a query string you create a QueryBuilder instance and add strings to your query like below:

```python
def main():
    # ...
    # Creating query for Influx, see example:
    # query = 'from(bucket:"bucket_name") \
    #           |> range(start: -10m) \
    #           |> filter(fn:(r) => r._measurement == "my_measurement") \
    #           |> filter(fn: (r) => r.location == "Prague") \
    #           |> filter(fn:(r) => r._field == "temperature" )'
    qb = QueryBuilder(bucket=influx_db.influx_bucket, start_range='-20d')
    qb.append_filter('_measurement', 'fx-1', 'or')
    qb.append_filter('_measurement', 'mx-1')
```

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
