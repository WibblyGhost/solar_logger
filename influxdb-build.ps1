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
