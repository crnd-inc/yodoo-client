#!/bin/bash


ODOO_PIDFILE="${ODOO_PIDFILE:-/var/run/odoo.pid}";
echo "odoo_infrastructure_token = qwerty" >> /opt/odoo/conf/odoo.conf
echo "server_wide_modules = base,web,odoo_infrastructure_client" >> /opt/odoo/conf/odoo.conf
odoo-helper server run --coverage -- --pidfile=$ODOO_PIDFILE &

sleep 5;
ODOO_PID="$(cat $ODOO_PIDFILE)";

odoo-helper exec python -m unittest run_tests.py

kill $ODOO_PID
