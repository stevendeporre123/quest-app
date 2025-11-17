# Deployment Guide

This document describes how to build and run Quest inside Docker and how to publish it behind an existing Traefik reverse proxy on EC2.

## 1. Prerequisites

- Docker Engine and Docker Compose v2 on the EC2 host.
- Existing Traefik container that exposes the external network named `traefik` (create it once using `docker network create traefik`).
- Access to the secrets the app needs (OpenAI keys, etc.). You can either keep
  them in a local `.env` file when running `docker compose` yourself or inject
  them through your orchestrator (Portainer, ECS, ...).

## 2. Build the image

```bash
docker compose build
```

The Dockerfile installs the requirements and defaults `QUEST_DB_PATH` to `/data/quest.db`. The `/data` directory is exposed as a volume so the SQLite database and uploaded source files survive container restarts. The compose file also references the published image `ghcr.io/stevendeporre123/quest-app:${QUEST_IMAGE_TAG:-main}` so Portainer and other orchestrators can pull a ready-made build. If you need a different tag, set `QUEST_IMAGE_TAG` in your stack (for example `QUEST_IMAGE_TAG=v1.2.3`).

## 3. Persistent storage

The provided `docker-compose.yml` mounts the named volume `quest_data` at `/data`. Besides the SQLite database, uploads are written to `/data/uploads` (configurable with `QUEST_STORAGE_DIR`). If you already have a `quest.db`, copy it to a safe place and restore it after the first run:

```bash
docker run --rm -v quest_data:/data -v "$PWD:/backup" alpine \
  cp /backup/quest.db /data/quest.db
```

## 4. Running with Traefik

Edit `docker-compose.yml` and replace `quest.example.com` with your real hostname. The Traefik labels assume an entrypoint named `websecure` and a certificate resolver named `letsencrypt`; update them if your Traefik configuration uses different names.

Start the service:

```bash
docker compose up -d
```

Traefik will automatically route HTTPS traffic to the Quest container and handle TLS termination.

## 5. Environment variables

The container only needs an `OPENAI_API_KEY` besides the `QUEST_*` paths defined
in `docker-compose.yml`. Supply it via whatever mechanism fits your deployment:

- When running `docker compose` directly, add it to a local `.env` file so
  Compose can interpolate `${OPENAI_API_KEY}` (and optionally `QUEST_IMAGE_TAG`)
  inside the service definition.
- When running the stack inside Portainer (or another orchestrator), configure
  `OPENAI_API_KEY` (and optionally `QUEST_IMAGE_TAG`) in the environment
  variable editor. The compose file already exposes them through the
  `environment` section, so no `.env` file is required.

Add any future secrets to the compose file in the same fashion so they can be
overridden either by `.env` or by the orchestration layer.

## 6. Updating

1. Pull or copy the latest application code.
2. Rebuild and restart:

```bash
docker compose build quest
docker compose up -d
```

The named volume keeps the database intact between deployments.

## 7. Troubleshooting

- Verify the Traefik network exists (`docker network ls`). If not, create it and restart Traefik before launching Quest.
- Check container logs with `docker compose logs -f quest`.
- Ensure filesystem permissions allow the container to create `/data/quest.db` and `/data/uploads` on first boot; the named volume handles this automatically.

You can adapt these steps to other orchestration tools (ECS, Nomad, etc.) by reusing the same Docker image and environment variables.
