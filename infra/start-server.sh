#!/usr/bin/env bash
set -euo pipefail

cd /srv/drewcraft/current
rm -rf world logs terrain-diffusion-models terrain-diffusion-cache
rm -f ops.json whitelist.json banned-ips.json banned-players.json
ln -s /srv/drewcraft/persistent/world world
ln -s /srv/drewcraft/logs logs
ln -s /srv/drewcraft/persistent/terrain-diffusion-models terrain-diffusion-models
ln -s /srv/drewcraft/persistent/terrain-diffusion-cache terrain-diffusion-cache
ln -s /srv/drewcraft/persistent/operator/ops.json ops.json
ln -s /srv/drewcraft/persistent/operator/whitelist.json whitelist.json
ln -s /srv/drewcraft/persistent/operator/banned-ips.json banned-ips.json
ln -s /srv/drewcraft/persistent/operator/banned-players.json banned-players.json

export JAVA_HOME=/opt/drewcraft/java
export PATH="$JAVA_HOME/bin:$PATH"
exec ./run.sh nogui
