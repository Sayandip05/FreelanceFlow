#!/usr/bin/env bash
set -e
git pull
docker compose --profile app up -d --build
