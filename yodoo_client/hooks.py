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


def module_db_initialize(cr):
    original_module_db_initialize(cr)
    cr.execute("""
        UPDATE ir_module_module
        SET state = 'to install'
        WHERE name IN (
            'yodoo_client',
            'base_setup'
        );
    """)


def _post_load_hook():
    if config.get('yodoo_db_filter', False):
        http.db_filter = db_filter

    # Make autoinstall of yodoo_client
    odoo.modules.db.initialize = module_db_initialize
