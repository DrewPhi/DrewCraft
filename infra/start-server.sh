#!/usr/bin/env bash
set -euo pipefail

cd /srv/drewcraft/current
rm -rf world logs terrain-diffusion-models terrain-diffusion-cache
rm -f ops.json whitelist.json banned-ips.json banned-players.json

# Keep the RCON secret outside immutable releases. The controller uses RCON
# only on localhost to coordinate idle pregeneration; it is never firewall-
# exposed. A persistent properties file prevents release activation from
# silently disabling the coordinator.
if [[ ! -f /srv/drewcraft/persistent/server.properties ]]; then
  cp server.properties /srv/drewcraft/persistent/server.properties
fi
rcon_password="$(tr -d '\r\n' </etc/drewcraft/rcon-password)"
if [[ -z "$rcon_password" ]]; then
  echo "missing /etc/drewcraft/rcon-password" >&2
  exit 1
fi
sed -i -E '/^(enable-rcon|rcon\.port|rcon\.ip|rcon\.password)=/d' /srv/drewcraft/persistent/server.properties
printf 'enable-rcon=true\nrcon.port=25575\nrcon.ip=127.0.0.1\nrcon.password=%s\n' "$rcon_password" >>/srv/drewcraft/persistent/server.properties
sed -i -E '/^level-type=/d' /srv/drewcraft/persistent/server.properties
printf 'level-type=drewcraft\\:terrain_diffusion_scale_3\n' >>/srv/drewcraft/persistent/server.properties
managed_datapack=/srv/drewcraft/current/datapacks/drewcraft-structures
world_datapack=/srv/drewcraft/persistent/world/datapacks/drewcraft-structures
if [[ ! -f "$managed_datapack/pack.mcmeta" ]]; then
  echo "missing managed DrewCraft structures datapack" >&2
  exit 1
fi
mkdir -p /srv/drewcraft/persistent/world/datapacks
if [[ ! -e "$world_datapack" ]]; then
  cp -a "$managed_datapack" "$world_datapack"
elif ! diff -rq "$managed_datapack" "$world_datapack" >/dev/null; then
  echo "DrewCraft structures datapack differs from the world; refusing mixed worldgen" >&2
  exit 1
fi
python3 /srv/drewcraft/bin/worldgen_guard.py --prepare
rm -f server.properties
ln -s /srv/drewcraft/persistent/server.properties server.properties
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
