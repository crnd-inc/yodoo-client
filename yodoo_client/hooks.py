import re
import odoo
from odoo import http
from odoo.tools import config

original_db_filter = http.db_filter
original_module_db_initialize = odoo.modules.db.initialize


def db_filter(dbs, httprequest=None):
    httprequest = httprequest or http.request.httprequest
    dbs = original_db_filter(dbs, httprequest=httprequest)
    db_header = httprequest.environ.get('HTTP_X_ODOO_DBFILTER')
    if not db_header:
        return dbs
    return [db for db in dbs if re.match(db_header, db)]


def make_addons_to_be_installed(cr, addons):
    """ update addons state to 'to install'

        :param list addons: List of addons to install
    """
    cr.execute("""
        UPDATE ir_module_module
        SET state='to install'
        WHERE name in %(to_install)s;
    """, {
        'to_install': tuple(addons),
    })


def ensure_installing_addons_dependencies(cr):
    # Ensure dependencies of auto-installed addons will be installed on
    # database creation
    while True:
        cr.execute("""
            SELECT array_agg(m.name)
            FROM ir_module_module AS m
            WHERE m.state != 'to install'
                AND EXISTS (
                SELECT 1
                FROM ir_module_module_dependency AS d
                JOIN ir_module_module msuper ON (d.module_id = msuper.id)
                WHERE d.name = m.name
                    AND msuper.state = 'to install'
                );
        """)
        to_install = cr.fetchone()[0]
        if not to_install:
            break
        make_addons_to_be_installed(cr, to_install)

    # Install recursively all auto-installing modules
    # (one more time, after yodoo_auto_installed addons installed)
    while True:
        cr.execute("""
            SELECT array_agg(m.name)
            FROM ir_module_module AS m
            WHERE m.auto_install
              AND state != 'to install'
              AND NOT EXISTS (
                  SELECT 1
                  FROM ir_module_module_dependency AS d
                  JOIN ir_module_module AS mdep ON (d.name = mdep.name)
                  WHERE d.module_id = m.id
                  AND mdep.state != 'to install'
              );
        """)
        to_auto_install = cr.fetchone()[0]
        if not to_auto_install:
            break
        make_addons_to_be_installed(cr, to_auto_install)


def module_db_initialize(cr):
    original_module_db_initialize(cr)

    make_addons_to_be_installed(cr, ['yodoo_client'])

    auto_install_addons = config.get('yodoo_auto_install_addons', '')
    auto_install_addons = [a.strip() for a in auto_install_addons.split(',')]
    if auto_install_addons:
        make_addons_to_be_installed(cr, auto_install_addons)

    ensure_installing_addons_dependencies(cr)


def _post_load_hook():
    if config.get('yodoo_db_filter', False):
        http.db_filter = db_filter

    # Make autoinstall of yodoo_client
    odoo.modules.db.initialize = module_db_initialize
