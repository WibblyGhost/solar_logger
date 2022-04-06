# NOTES
# $(pwd) - Expands to working directory on Linux or Mac
# ${pwd} - Expands to working directory on Windows IN POWERSHELL

$CurrentDir = ${pwd}
$EnvFile = "solar.env"
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
