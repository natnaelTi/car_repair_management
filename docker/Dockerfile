# syntax=docker/dockerfile:1.6
#
# Custom frappe/erpnext image with car_repair_management baked in.
#
# Build context MUST be the frappe-bench root so that
# ./apps/car_repair_management/ is reachable from the COPY below.
#
# Usage (from frappe-bench root):
#   docker build \
#     -f apps/car_repair_management/docker/Dockerfile \
#     -t car-repair-management:v15.79.0 \
#     .
#
# After building, see apps/car_repair_management/docker/README.md for how to
# point your frappe_docker compose stack at this image.

ARG FRAPPE_VERSION=v15.79.0
FROM frappe/erpnext:${FRAPPE_VERSION}

USER root

# Copy the app into the bench
COPY --chown=frappe:frappe ./apps/car_repair_management \
     /home/frappe/frappe-bench/apps/car_repair_management

# Make sure node/yarn are usable for the frontend build
ENV PATH="/home/frappe/.nvm/versions/node/v18.18.2/bin:${PATH}"

USER frappe
WORKDIR /home/frappe/frappe-bench

# 1. Install the Python package into the bench virtualenv
RUN /home/frappe/frappe-bench/env/bin/pip install --no-cache-dir \
        -e apps/car_repair_management

# 2. Register the app with bench so `bench build` finds it
RUN bash -lc 'grep -qxF car_repair_management sites/apps.txt 2>/dev/null \
        || echo "car_repair_management" >> sites/apps.txt'

# 3. Build the Vue 3 SPA. We use yarn so the lockfile is honored.
RUN bash -lc 'cd apps/car_repair_management/frontend \
        && yarn install --frozen-lockfile \
        && yarn build'

# 4. Run bench build so the asset symlinks land under sites/assets/
RUN bash -lc 'bench build --app car_repair_management'

# Smoke check: assets must exist in the image so they show up in the
# anonymous sites/assets volume on first start.
RUN test -d /home/frappe/frappe-bench/sites/assets/car_repair_management/frontend/assets \
    && ls /home/frappe/frappe-bench/sites/assets/car_repair_management/frontend/assets/ \
        | grep -E '^index-.*\.(js|css)$' >/dev/null
