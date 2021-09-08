#!/bin/bash

SCRIPT=$0;
SCRIPT_NAME=$(basename "$SCRIPT");
SCRIPT_DIR=$(readlink -f "$(dirname $SCRIPT)");
WORK_DIR=$(pwd);

set -e;

(
    cd "$SCRIPT_DIR" && \
    odoo-helper start --coverage -- -p 8069 --http-interface=localhost && \
    sleep 5 && \
    odoo-helper exec python -m unittest tests && \
    odoo-helper stop && \
    odoo-helper exec coverage combine && \
    odoo-helper exec coverage report && \
    odoo-helper stop
)
