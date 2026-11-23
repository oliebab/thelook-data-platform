#!/bin/bash
if [ ! -f /opt/thelook-setup-done ]; then
  export DEBIAN_FRONTEND=noninteractive
  apt-get update
  apt-get install -y git make jq unzip python3-pip python3-venv pipx
  add-apt-repository -y ppa:deadsnakes/ppa
  apt-get update
  apt-get install -y python3.12 python3.12-venv
  curl -fsSL https://get.docker.com | sh
  PIPX_HOME=/opt/pipx PIPX_BIN_DIR=/usr/local/bin pipx install poetry
  touch /opt/thelook-setup-done
fi
