# Deployment Guide

This document describes how to build and run Quest inside Docker and how to publish it behind an existing Traefik reverse proxy on EC2.

## 1. Prerequisites

- Docker Engine and Docker Compose v2 on the EC2 host.
- Existing Traefik container that exposes the external network named `traefik` (create it once using `docker network create traefik`).
- `.env` file in the project root that contains the same secrets the app uses locally (OpenAI keys, etc.).

## 2. Build the image

```bash
docker compose build
```

The Dockerfile installs the requirements and defaults `QUEST_DB_PATH` to `/data/quest.db`. The `/data` directory is exposed as a volume so the SQLite database survives container restarts.

## 3. Persistent storage

The provided `docker-compose.yml` mounts the named volume `quest_data` at `/data`. If you already have a `quest.db`, copy it to a safe place and restore it after the first run:

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

All environment variables from `.env` are passed to the container. Add any extra values to `.env` (for example `OPENAI_API_KEY`, `AZURE_OPENAI_ENDPOINT`, etc.). The `QUEST_DB_PATH` variable is set inside `docker-compose.yml`; change it if you prefer a different mount point.

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
- Ensure filesystem permissions allow the container to create `/data/quest.db` on first boot; the named volume handles this automatically.

You can adapt these steps to other orchestration tools (ECS, Nomad, etc.) by reusing the same Docker image and environment variables.
