import re
from odoo import http
from odoo.tools import config

original_db_filter = http.db_filter


def db_filter(dbs, httprequest=None):
    httprequest = httprequest or http.request.httprequest
    dbs = original_db_filter(dbs, httprequest=httprequest)
    db_header = httprequest.environ.get('HTTP_X_ODOO_DBFILTER')
    if not db_header:
        return dbs
    return [db for db in dbs if re.match(db_header, db)]


def _post_load_hook():
    if config.get('yodoo_db_filter', False):
        http.db_filter = db_filter
