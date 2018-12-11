#!/bin/bash

SCRIPT=$0;
SCRIPT_NAME=$(basename "$SCRIPT");
SCRIPT_PATH=$(readlink -f "$SCRIPT");
SCRIPT_DIR=$(dirname "$SCRIPT_PATH");
WORKDIR=$(pwd);

set -e;

# chechout to migration script dirto be sure that right odoo-helper config file
# will be used 
cd "$SCRIPT_DIR";

for dbname in $(odoo-helper db list); do
    if ! odoo-helper postgres psql --single-transaction --set="ON_ERROR_STOP=1" -d "$dbname" -f "$SCRIPT_DIR"/migrate.sql; then
        echo "ERROR: migration of database '$dbname' failed!";
    else
        echo "OK: database '$dbname' migrated successfully!";
    fi
done

# Checkout to previous work directory
cd "$WORKDIR";

