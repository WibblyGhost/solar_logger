# NOTES
# $(pwd) - Expands to working directory on Linux or Mac
# ${pwd} - Expands to working directory on Windows IN POWERSHELL

$CurrentDir = ${pwd}
$EnvFile = ".env"
$IsFromDockerHub = $TRUE
$VersionTag = "0.0.1"


if ($IsFromDockerHub == $FALSE) {
    # Start by building an image of SolarLogger localy
    docker build . -f solar.dockerfile -t solar_logger_local
}

# Before running the Docker images I would suggest creating the config and output volumes first
# Otherwise the config.ini won't get copied across
mkdir $CurrentDir/docker_solar_logger/output
mkdir $CurrentDir/docker_solar_logger/config

# CONFIG VOLUMES
# docker volume create --driver local \
# --opt type=none \
# --opt device="${pwd}/docker_solar_logger/config" \
# --opt o=bind \
# SolarLogger-Config

docker volume create --driver local --opt type=none --opt device="$CurrentDir/docker_solar_logger/config" --opt o=bind SolarLogger-Config

# OUTPUT VOLUMES
# docker volume create --driver local \
# --opt type=none \
# --opt device="${pwd}/docker_solar_logger/output" \
# --opt o=bind \
# SolarLogger-Output

docker volume create --driver local --opt type=none --opt device="$CurrentDir/docker_solar_logger/output" --opt o=bind SolarLogger-Output


# Run the Docker image with an environment file, output folder and config folder
# docker run -d \
# --name solar_logger \
# --env-file ".env" \
# --volume "SolarLogger-Config:/app/config" \
# --volume "SolarLogger-Output:/app/output" \
# solar_logger_local

if ($IsFromDockerHub) {
    # If the image is built from Docker hub
    docker run -d --name solar_logger_hub --env-file $EnvFile --volume "SolarLogger-Config:/app/config" --volume "SolarLogger-Output:/app/output" wibblyghost/solar_logger:$VersionTag
} else {
    # If the image is built locally
    docker run -d --name solar_logger_local --env-file $EnvFile --volume "SolarLogger-Config:/app/config" --volume "SolarLogger-Output:/app/output" solar_logger_local
}
