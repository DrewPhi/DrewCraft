#!/usr/bin/env bash
set -euo pipefail

# DrewCraft production-host bootstrap for Ubuntu ARM64.
# Run once as root on a freshly provisioned VM. It deliberately creates no
# cloud resources and enables no autoscaling.

if [[ "$(id -u)" -ne 0 ]]; then
  echo "run as root" >&2
  exit 1
fi
if [[ "$(uname -m)" != "aarch64" ]]; then
  echo "DrewCraft ARM profile requires aarch64; got $(uname -m)" >&2
  exit 1
fi

JAVA_URL='https://github.com/adoptium/temurin21-binaries/releases/download/jdk-21.0.12.1%2B1/OpenJDK21U-jre_aarch64_linux_hotspot_21.0.12.1_1.tar.gz'
JAVA_SHA='14be1f35ebdbd1f6e8d57eb911a3ffb74d6d9aa255abc5daf2b1302002cf2cf2'
JAVA_SIZE='51149460'

apt-get update
DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends ca-certificates curl python3 ufw tar

if ! id drewcraft >/dev/null 2>&1; then
  useradd --system --create-home --home-dir /srv/drewcraft --shell /usr/sbin/nologin drewcraft
fi
install -d -o drewcraft -g drewcraft /srv/drewcraft/{releases,staging,persistent/world,backups,logs,state,bin}
install -d -o root -g root /opt/drewcraft/runtime/java-21.0.12.1+1

tmp="$(mktemp)"
trap 'rm -f "$tmp"' EXIT
curl --fail --location --retry 3 --output "$tmp" "$JAVA_URL"
[[ "$(stat -c%s "$tmp")" == "$JAVA_SIZE" ]]
echo "$JAVA_SHA  $tmp" | sha256sum -c -
rm -rf /opt/drewcraft/runtime/java-21.0.12.1+1/*
tar -xzf "$tmp" -C /opt/drewcraft/runtime/java-21.0.12.1+1
java_bin="$(find /opt/drewcraft/runtime/java-21.0.12.1+1 -type f -name java | head -n 1)"
[[ -n "$java_bin" ]]
ln -sfn "$(dirname "$(dirname "$java_bin")")" /opt/drewcraft/java
/opt/drewcraft/java/bin/java -version

cat >/srv/drewcraft/bin/start-server.sh <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
cd /srv/drewcraft/current
rm -rf world logs
ln -s /srv/drewcraft/persistent/world world
ln -s /srv/drewcraft/logs logs
export JAVA_HOME=/opt/drewcraft/java
export PATH="$JAVA_HOME/bin:$PATH"
exec ./run.sh nogui
EOF
chmod 0755 /srv/drewcraft/bin/start-server.sh
chown root:root /srv/drewcraft/bin/start-server.sh

# SSH remains available. Minecraft and the read-only release-health endpoint
# are the only new public ports.
ufw allow OpenSSH
ufw allow 25565/tcp
ufw allow 25566/tcp
ufw --force enable

echo "Host base ready. Install infra/drewcraft.service and infra/drewcraft-health.service, then deploy a verified release with infra/serverctl.py."
