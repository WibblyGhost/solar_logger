# Solar Logger

## Info

This project is a multi-step program which relies on a MQTT backend to read information from an Outback solar controller which sends statistics of current battery status, input voltages etc. This program subscribes to the MQTT broker to retrieve the information broadcast and deciphers the raw byte streams into a readable form. It then converts the data into points to allow insertion into a time series database (InfluxDB) where the data can be stored, modeled and queried. The database will link to a Grafana website which will graph, model and compare the data on a privately accessible site.

The program makes use of multi-threaded applications for receiving MQTT data packets and uploading the packets into InfluxDB. This is done by transfering packets from one thread into the other by the use of `Queues`.

## InfluxDB Setup

This project comes with a mostly pre-built Influx instance that you can run up or copy to a Docker server. All Influx configurations will be written to the folder `docker_influxdb`. If this is your first time running InfluxDB I would suggest uncommenting the following code in the `docker-compose.yml` and copying specified `.env` file into the base directory. 
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

To start, fill out the `.env` template file with personal secrets and copy them to the base directory. Then after running a Docker compose it will use the environmental variables to start the service and start writing data into Influx. If any errors occur then look through the Docker log files.

## Contents

### Logging

All programs below are implemented with a file logger which can be configured through the config.ini file, this can be used for program info or debugging purposes. If file logging is enabled all logs will be written in the `output` folder although if using within a Docker instance it will be written to `docker_output` instead.

**Note:** by default a `docker_output` volume is created. If you're not using file logging, comment out the following code in the `docker-compose.yml`:
```yml
SolarLogger:
    volumes:
      - ./docker_output:/app/output:rw
```

### Configurations

All debugging and querying options can be changed through the config file. If file logging is set to false then the generated output will be set to only use standard output. The file logging uses rotational logging meaning that it will create a new log after a set file size has been reached.

```ini
[influx_debugger]
file_logging    = true
; Can be set to" time_based, size_based
log_rotation    = time_based
; Logging levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
debug_level     = DEBUG
; Only needed if file logging is true
file_location   = output/
file_name       = influx_logs.log
format          = %%(asctime)s, %%(name)s, %%(levelname)s, %%(message)s
dateformat      = %%d/%%m/%%Y, %%H:%%M:%%S
; Rotating file loggers require the following configs
max_file_no     = 5
time_cutover    = "midnight"
max_file_bytes  = 5242880


[solar_debugger]
file_logging    = true
; Can be set to" time_based, size_based
log_rotation    = time_based
;Logging levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
debug_level     = DEBUG
; Only needed if file logging is true
file_location   = output/
file_name       = solar_logs.log
format          = %%(asctime)s, %%(name)s, %%(levelname)s, %%(message)s
dateformat      = %%d/%%m/%%Y, %%H:%%M:%%S
; Rotating file loggers require the following configs
max_file_no     = 5
time_cutover    = "midnight"
max_file_bytes  = 5242880


[query_settings]
; Can be either 'csv, 'flux' or 'stream'
query_mode      = flux
; Following three values are only required for CSV's
csv_location    = output/
csv_name        = query_result.csv
csv_mode        = w
```

___

## Program Files

### Solar Logger

Defines the program that deals with subscribing to the solar controller's broker using MQTT, decodes the raw packets, and inputs the data points into a time series database *(Influx DB)*.

**Usage:** To use this program you must set up an Influx controller which connects to the Influx database and also set up a MQTT subscriber. The MQTT subscriber requires an Influx controller instance for it to run since it uses the controller to write data as it receives the data points.

Firstly create a MQTT listening service that runs indefinitely to retrieve data points from the MQTT broker, from which will then insert the data points into the Influx database.

```python
    def run_mqtt_listener(self) -> None:
        """
        Initial setup for the MQTT connector, connects to MQTT broker
        and failing to connect will exit the program
        """
        logging.info("Connecting to MQTT broker")
        self._mqtt_client.username_pw_set(
            username=self._mqtt_secrets["mqtt_user"],
            password=self._mqtt_secrets["mqtt_token"],
        )
        self._mqtt_client.tls_set(cert_reqs=ssl.CERT_NONE)
        self._mqtt_client.tls_insecure_set(True)
        self._mqtt_client.on_connect = self._on_connect
        try:
            self._mqtt_client.connect(
                host=self._mqtt_secrets["mqtt_host"],
                port=self._mqtt_secrets["mqtt_port"],
            )
        except Exception as err:
            print(
                type(self._mqtt_secrets["mqtt_host"]),
                type(self._mqtt_secrets["mqtt_port"]),
            )
            logging.critical("Failed to connect to MQTT broker")
            raise err
        self._mqtt_client.on_message = self._on_message
        self._mqtt_client.loop_forever()
```

The MQTT runtime will call on the `MQTTDecoder` class from **mqtt_classes.py** which will listen and push data points onto a `Queue`.

`_on_connect()` runs when the MQTT subscriber firstly connects to the MQTT broker, in our case it uses the secrets file *(excluded passwords file)*  to choose what subscription to listen to.

`_on_message()` runs every time the MQTT subscriber receives a message from the broker.

Afterwards create an Influx controller instance and make an active connection to given Influx server.

```python
    def influx_startup(self) -> None:
        """
        Defines the initialization of the Influx connector,
        invoking the connection to the InfluxDB and write API
        """
        logging.info("Attempting to connect to InfluxDB server")
        client = None
        try:
            client = InfluxDBClient(
                url=self._influx_url,
                token=self._influx_token,
                org=self.influx_org
            )
            client.ready()
            logging.info("Successfully connected to InfluxDB server")
        except Exception as err:
            logging.critical("Failed to connect InfluxDB server")
            raise err
        finally:
            self.influx_client = client
```

When messages are received from the MQTT broker, they are then decoded, sorted and uploaded through the `InfluxConnector` class.

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
