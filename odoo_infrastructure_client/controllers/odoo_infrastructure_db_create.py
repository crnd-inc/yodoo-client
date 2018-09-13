import logging

from contextlib import closing

from odoo import http, fields
from odoo.sql_db import db_connect
from odoo.http import Response
from odoo.service import db as service_db
from odoo.modules import db as modules_db
from ..utils import require_saas_token, conflict, not_satisfiable

_logger = logging.getLogger(__name__)


class OdooInfrastructureDBCreate(http.Controller):

    @http.route(
        '/saas/client/db/create',
        type='http',
        auth='none',
        metods=['POST'],
        csrf=False
    )
    @require_saas_token
    def client_db_create(self,
                         dbname=None,
                         demo=False,
                         lang='en_US',
                         user_password='admin',
                         user_login='admin',
                         country_code=None,
                         template_dbname=None,
                         **params):
        dbname = dbname.strip() or 'db_created_%s' % fields.Datetime.now()
        try:
            service_db._create_empty_database(dbname)
        except service_db.DatabaseExists as bd_ex:
            return conflict(description=str(bd_ex))
        service_db._initialize_db(
            id, dbname, demo, lang, user_password, user_login, country_code)
        db = db_connect(dbname)
        with closing(db.cursor()) as cr:
            db_init = modules_db.is_initialized(cr)
        if not db_init:
            return not_satisfiable(description='Database not initialized.')
        return Response('successfully', status=200)
