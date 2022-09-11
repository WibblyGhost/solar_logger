# Solar Logger

![slice3](https://user-images.githubusercontent.com/47839859/161478218-66dbca5d-5277-479e-8144-1c017c92fbd3.png)
<!-- [![Pylint](https://github.com/WibblyGhost/solar_logger/actions/workflows/pylint.yml/badge.svg)](https://github.com/WibblyGhost/solar_logger/actions/workflows/pylint.yml)
[![Docker Package Deployment](https://github.com/WibblyGhost/solar_logger/actions/workflows/docker-publish.yml/badge.svg)](https://github.com/WibblyGhost/solar_logger/actions/workflows/docker-publish.yml) -->
[![Docker Package Deployment](https://github.com/WibblyGhost/solar_logger/actions/workflows/workflow.yml/badge.svg)](https://github.com/WibblyGhost/solar_logger/actions/workflows/workflow.yml)

## Info

This project is a multi-step program which relies on a MQTT backend to read information from an Outback solar controller which sends statistics of current battery status, input voltages etc. This program subscribes to the MQTT broker to retrieve the information broadcast and deciphers the raw byte streams into a readable form. It then converts the data into points to allow insertion into a time series database (InfluxDB) where the data can be stored, modeled and queried. The database will link to a Grafana website which will graph, model and compare the data on a privately accessible site.

The program makes use of multi-threaded applications for receiving MQTT data packets and uploading the packets into InfluxDB. This is done by transferring packets from one thread into the other by the use of `Queues`. The MQTT listener and Influx `write_api` both run concurrently.

## Docker Setup

To make installation easy there is a PowerShell file that will run the Docker pull from my hub repository, and run all basic configurations needed to start SolarLogger. If you want to customize images or run the other programs held within this repository I would recommend editing and using the `docker-compose.yml`. You can pull my Docker image using the image tag `wibblyghost/solar-logger`.

Both `docker-compose.yml` and `solar-logger-build.ps1` can be customized to your personal preferences.

**Note:** To run the SolarLogger you require a `.env` file in the same directory that you run the `solar-logger-build.ps1` file, otherwise change the `$EnvFile` variable to reflect the true path.

```powershell
# NOTES
# $(pwd) - Expands to working directory on Linux or Mac
# ${pwd} - Expands to working directory on Windows IN POWERSHELL

$CurrentDir = ${pwd}
$EnvFile = ".env"
$IsFromDockerHub = $TRUE
$VersionTag = "latest"
$RestartMode = "unless-stopped"


if (!(${IsFromDockerHub})) {
    # Start by building an image of SolarLogger locally
    docker build . -f solar.dockerfile -t solar-logger-local
}

# Before running the Docker images I would suggest creating the config and output volumes first
# Otherwise the config.ini won't get copied across
if (!(Test-Path -Path "${CurrentDir}/docker-solar-logger/output")) {
    mkdir -p "${CurrentDir}/docker-solar-logger/output"
}
if (!(Test-Path -Path "${CurrentDir}/docker-solar-logger/config")) {
    mkdir -p "${CurrentDir}/docker-solar-logger/config"
}


# CONFIG VOLUMES
# docker volume create \
docker volume create --driver local --opt type=none --opt device="${CurrentDir}/docker-solar-logger/config" --opt o=bind SolarLogger-Config

# OUTPUT VOLUMES
docker volume create --driver local --opt type=none --opt device="${CurrentDir}/docker-solar-logger/output" --opt o=bind SolarLogger-Output


# Run the Docker image with an environment file, output folder and config folder
if (${IsFromDockerHub}) {
    # If the image is built from Docker hub
    docker run -d --name solar-logger --restart="${RestartMode}" --env-file "${EnvFile}" --volume "SolarLogger-Config:/app/config" --volume "SolarLogger-Output:/app/output" wibblyghost/solar-logger:"${VersionTag}"
} else {
    # If the image is built locally
    docker run -d --name solar-logger --restart="$RestartMode" --env-file "${EnvFile}" --volume "SolarLogger-Config:/app/config" --volume "SolarLogger-Output:/app/output" solar-logger-local
}
```

In a recent update I've also added a script `influxdb-build.ps1` to pull and create a InfluxDB image through docker also.

```PowerShell
# NOTES
# $(pwd) - Expands to working directory on Linux or Mac
# ${pwd} - Expands to working directory on Windows IN POWERSHELL

$CurrentDir = ${pwd}
$RestartMode = "unless-stopped"


# Before running the Docker images I would suggest creating the config and output volumes first
# Otherwise the config.ini won't get copied across
if (!(Test-Path -Path "${CurrentDir}/docker-influxdb/data-volume")) {
    mkdir -p "${CurrentDir}/docker-influxdb/data-volume"
}
if (!(Test-Path -Path "${CurrentDir}/docker-influxdb/config")) {
    mkdir -p "${CurrentDir}/docker-influxdb/config"
}

# Create docker volumes that mount to the current directory
# /var/lib/influxdb2
docker volume create --driver local --opt type=none --opt device="${CurrentDir}/docker-influxdb/data-volume" --opt o=bind InfluxDB-DataVolume
# /etc/influxdb2
docker volume create --driver local --opt type=none --opt device="${CurrentDir}/docker-influxdb/config" --opt o=bind InfluxDB-Config

# Run the build command and start InfluxDB
docker run -d --name influx-db -p 8086:8086 -p 8088:8088 --restart="${RestartMode}" --volume "InfluxDB-DataVolume:/var/lib/influxdb2" --volume "InfluxDB-Config:/etc/influxdb2" influxdb:2.1.1
```

## Logging

All programs below are implemented with a file logger which can be configured through the `config.ini` file, this can be used for program info or debugging purposes. If file logging is enabled all logs will be written in the `output` folder although if using within a Docker instance it will be written to `/docker-name/output` instead.

**Note:** By default a `/docker-name/output` volume is created.

## Solar Logger

### Setup

To start, fill out the `.env` template file with personal secrets and copy them to the base directory. Then after running a Docker compose it will use the environmental variables to start the service and start writing data into Influx. You can run the Docker build commands either through the `docker-compose.yml` or `solar-logger-build.ps1` files and both will mount a config and output volume under `/docker-solar-logger/`.

### Summary

The Solar Logger acts as a bridge between a **MQTT** broker and a *time series database* **InfluxDB**. It does this by subscribing to the MQTT broker, decoding the packets and uploading the results to Influx.

The program makes use of multi-threading to keep listening and writing services active concurrently. The MQTT and Influx methods both make use of threading through the `solar_logger` runtime.

**Usage:** To use this program you must set up an Influx controller which connects to the Influx database and also set up a MQTT subscriber. The MQTT subscriber requires an Influx controller instance for it to run since it uses the controller to write data as it receives the data points. There are already pre-defined classes that I've create that will help you achieve this.

### Code Run Through

#### MQTT

Firstly we create a new thread for the MQTT listening service to run on, then initialize the service with all required connection credentials. This can be done through the `SecretStore` and `MqttConnector` class.

Then we can run the MQTT listening service by creating a *MQTT Client*.

```python
secret_store = SecretStore(has_mqtt_access=True)
mqtt_connector = MqttConnector(
    secret_store=secret_store,
)
mqtt_client = mqtt_connector.get_mqtt_client()
```

Then you must start the listening service.

```python
mqtt_client.loop_start()
```

**Note:** `loop_start()` actually creates another thread since on-top of out already created `MQTT-Thread`. But due to the complexity of setting up MQTT's `read_loop()`, I've decided to keep the separate thread instead.

From this point onwards the threads just works in the background, listening, decoding packets and pushing the packets onto a globally available `Queue`.

**Notes:**
`_on_connect()` runs when the MQTT subscriber firstly connects to the MQTT broker to choose what subscription to listen to.

`_on_message()` runs every time the MQTT subscriber receives a message from the broker.

#### Influx

This part of the program is much simpler than the MQTT listener service. Firstly we create another new thread for the InfluxDB service to run on, then initialize the service with all required connection credentials. This can be done through the `SecretStore` and `InfluxConnector` class.

```python
secret_store = SecretStore(has_influx_access=True)
influx_connector = InfluxConnector(secret_store=secret_store)
```

Since InfluxDB doesn't require an ongoing connection we only need to make a connection when *writing* or *querying* the server.

We do however run a quick `health_check()` on creation to check the endpoint is alive.

 ```python
 influx_connector.health_check()
 ```

Following the check we run a blocking loop which constantly checks for items in the `Queue` and writes the points to the Influx server.

```python
queue_package: QueuePackage = THREADED_QUEUE.get(timeout=1.0)
try:
    influx_connector.write_points(queue_package=queue_package)
```


## InfluxDB

### Setup

This project comes with a mostly pre-built InfluxDB instance that you can run up or copy to a Docker server. This can be run through the `docker-compose.yml` or `influxdb-build.ps1` and customized to accept initial setup variables. All Influx configurations will be written to the folder `/docker-influxdb/`. *(If this is your first time running the `docker-compose.yml` I would suggest uncommenting the following code.)* After configuring InfluxDB all following Docker restarts should keep their configs and data through the mounted volumes in `/docker-influxdb/`.

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

## Influx Queries *(Docker Compose Only)*

### Summary

This is a simple program that is meant to provide minimal user experience to a pythonic way to Query an Influx database.

It contains methods to allow for different aggregation, sorting, range fields and more. The program will handle creating and running the queries.

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

## Configurations

All debugging and querying options can be changed through the config file. If file logging is set to false then the generated output will be set to only use standard output. The file logging uses rotational logging meaning that it will create a new log after a set file size has been reached.

```ini
[influx_debugger]
; Logging levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
debug_level     = INFO
file_logging    = true
; Log rotation can be set to time_based or size_based
log_rotation    = size_based
file_location   = output/
file_name       = influx_logs.log
format          = %%(asctime)s, %%(name)s, %%(levelname)s, %%(message)s
dateformat      = %%d/%%m/%%Y, %%H:%%M:%%S
; Rotating file loggers require the following configs
max_file_no     = 5
time_cutover    = "midnight"
max_file_bytes  = 5242880


[solar_debugger]
;Logging levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
debug_level     = INFO
file_logging    = true
; Log rotation can be set to time_based or size_based
log_rotation    = size_based
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
