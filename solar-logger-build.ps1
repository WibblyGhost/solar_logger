# NOTES
# $(pwd) - Expands to working directory on Linux or Mac
# ${pwd} - Expands to working directory on Windows IN POWERSHELL

$IsFromDockerHub = $TRUE

$CurrentDir = ${pwd}
$EnvFile = ".env"
$VersionTag = "latest"
$RestartMode = "unless-stopped"


if (!${IsFromDockerHub} -and !$Development) {
    # Start by building an image of SolarLogger locally
    docker build . -f solar-logger.dockerfile -t solar-logger-local
}

# Before running the Docker images I would suggest creating the config and output volumes first
# Otherwise the config.ini won't get copied across
if (!(Test-Path -Path "${CurrentDir}/output")) {
    mkdir -p "${CurrentDir}/output"
}
if (!(Test-Path -Path "${CurrentDir}/config")) {
    mkdir -p "${CurrentDir}/config"
}


# CONFIG VOLUMES
# docker volume create \
docker volume create --driver local --opt type=none --opt device="${CurrentDir}/config" --opt o=bind SolarLogger-Config

# OUTPUT VOLUMES
docker volume create --driver local --opt type=none --opt device="${CurrentDir}/output" --opt o=bind SolarLogger-Output


# Run the Docker image with an environment file, output folder and config folder
if (${IsFromDockerHub}) {
    # If the image is built from Docker hub
    docker run -d --name solar-logger --restart="${RestartMode}" --env-file "${EnvFile}" --volume "SolarLogger-Config:/solarlogger/config" --volume "SolarLogger-Output:/solarlogger/output" wibblyghost/solar-logger:"${VersionTag}"
} else {
    # If the image is built locally
    docker build . -f solar-logger.dockerfile -t wibblyghost/solar-logger --target solar-logger -t solar-logger-local
    docker run -d --name solar-logger --restart="$RestartMode" --env-file "${EnvFile}" --volume "SolarLogger-Config:/solarlogger/config" --volume "SolarLogger-Output:/solarlogger/output" --network host solar-logger-local
}
