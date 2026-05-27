#!/usr/bin/env bash
# Instala Docker y Docker Compose plugin en Ubuntu 22.04/24.04 (EC2).
# Ejecutar en la instancia: bash deploy/ec2-bootstrap.sh
set -euo pipefail

if [[ "${EUID:-}" -ne 0 ]]; then
  echo "Ejecuta como root: sudo bash deploy/ec2-bootstrap.sh"
  exit 1
fi

export DEBIAN_FRONTEND=noninteractive

apt-get update -y
apt-get install -y ca-certificates curl gnupg git

if ! command -v docker >/dev/null 2>&1; then
  install -m 0755 -d /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
  chmod a+r /etc/apt/keyrings/docker.asc
  echo \
    "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
    $(. /etc/os-release && echo "${VERSION_CODENAME:-$VERSION_ID}") stable" \
    > /etc/apt/sources.list.d/docker.list
  apt-get update -y
  apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
fi

systemctl enable docker
systemctl start docker

# Usuario que invocó sudo (si aplica)
DEPLOY_USER="${SUDO_USER:-ubuntu}"
if id "$DEPLOY_USER" &>/dev/null; then
  usermod -aG docker "$DEPLOY_USER"
  echo "Usuario $DEPLOY_USER agregado al grupo docker (cierra sesión SSH y vuelve a entrar)."
fi

docker --version
docker compose version
echo "Bootstrap listo. Siguiente: clonar el repo, configurar .env e IotCore/, luego levantar el stack."
