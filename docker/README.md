# Custom Docker image for `car_repair_management`

This directory contains everything needed to bake the `car_repair_management`
app — including its built Vue 3 SPA — into a custom image based on
`frappe/erpnext`. It exists because the official `frappe_docker` setup uses
**separate anonymous volumes** for `sites/assets/` in the `backend` and
`frontend` containers. As a result, running `bench build` inside `backend`
populates assets that the `frontend` nginx container can never see, which
shows up as 404s for `/assets/car_repair_management/frontend/assets/*` and a
blank `/workshop` page.

Baking the assets into the image fixes this once and for all: when each
container starts, its anonymous `sites/assets` volume is initialized from
the image, so both containers end up with the SPA assets.

## What's here

| File | Purpose |
| --- | --- |
| `Dockerfile` | Builds `car-repair-management:v15.x.x` on top of `frappe/erpnext` |
| `compose.car-repair-management.yaml` | Compose override that swaps every Frappe service to the new image |

## Prerequisites

- A working `frappe_docker` checkout (the directory that holds your
  `compose.yaml` plus the various `overrides/*.yaml` files).
- Docker with BuildKit enabled (default on modern Docker).

## 1. Build the image

Run from the **frappe-bench root** (the directory that contains
`apps/car_repair_management`), so that the Dockerfile's `COPY ./apps/...`
finds the source tree:

```bash
docker build \
  --build-arg FRAPPE_VERSION=v15.79.0 \
  -f apps/car_repair_management/docker/Dockerfile \
  -t car-repair-management:v15.79.0 \
  .
```

Bump the tag (`-t`) and `FRAPPE_VERSION` together if you want to pin to a
different ERPNext release.

## 2. Wipe the stale `assets` volumes

The existing per-container anonymous `sites/assets` volumes are still going
to override the assets baked into the new image until they're removed.
**Stop the stack first**, then prune the assets volumes:

```bash
cd /path/to/frappe_docker
docker compose down

# List anonymous assets volumes (they're the ones with hash names mounted at
# /home/frappe/frappe-bench/sites/assets in either backend-1 or frontend-1).
docker volume ls --filter dangling=true

# Or, more targeted: remove every volume that ISN'T frappe_docker_sites,
# frappe_docker_logs, db-data, redis volumes, etc.
# Inspect first to be sure!
docker volume inspect <volume-name>

docker volume rm <backend-assets-volume-id> <frontend-assets-volume-id>
```

Do **not** delete `frappe_docker_sites`, `frappe_docker_db_data`, or your
Redis volumes — those hold your sites and database.

## 3. Bring the stack back up with the new image

Copy `compose.car-repair-management.yaml` into your `frappe_docker`
directory (or reference it by path), then:

```bash
docker compose \
  -f compose.yaml \
  -f overrides/compose.mariadb.yaml \
  -f overrides/compose.redis.yaml \
  -f compose.car-repair-management.yaml \
  up -d
```

(Adjust the override list to whatever your stack actually uses.)

## 4. Install the app on the site (one-time, only on a new site)

If the site doesn't already have `car_repair_management` installed:

```bash
docker compose exec backend bench --site <your-site> install-app car_repair_management
docker compose exec backend bench --site <your-site> migrate
docker compose exec backend bench --site <your-site> clear-cache
```

## 5. Verify

```bash
# Assets are present in the frontend container's view
docker compose exec frontend ls \
  /home/frappe/frappe-bench/sites/assets/car_repair_management/frontend/assets \
  | head

# A direct fetch returns 200
curl -I http://localhost:8080/assets/car_repair_management/frontend/manifest.json
```

Then load `http://<host>:8080/workshop` in a hard-refreshed browser.

## Rebuilding after code changes

Any time you change `car_repair_management` (Python, Vue, or both):

```bash
# 1. Rebuild the image
docker build \
  --build-arg FRAPPE_VERSION=v15.79.0 \
  -f apps/car_repair_management/docker/Dockerfile \
  -t car-repair-management:v15.79.0 \
  .

# 2. Recreate the assets volumes so they re-init from the new image
docker compose down
docker volume rm <backend-assets-volume-id> <frontend-assets-volume-id>
docker compose -f ... up -d

# 3. (Python changes only) migrate / clear cache as needed
docker compose exec backend bench --site <your-site> migrate
docker compose exec backend bench --site <your-site> clear-cache
```

The dynamic-asset-resolution work in `www/workshop.py` ensures that even
without rebuilding the image, the served HTML always points at whichever
hashed filenames are currently inside `sites/assets/car_repair_management/`.
The image just makes sure those files exist in both containers.
