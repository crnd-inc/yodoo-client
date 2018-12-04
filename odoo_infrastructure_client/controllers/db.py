import re
import json
import logging
from contextlib import closing

from odoo import http, api, registry, SUPERUSER_ID
from odoo.sql_db import db_connect
from odoo.http import Response
from odoo.service import db as service_db
from odoo.modules import db as modules_db

from ..utils import (
    require_saas_token,
    require_db_param,
    conflict,
    bad_request,
    server_error,
    prepare_db_statistic_data,
)

_logger = logging.getLogger(__name__)


class SAASClientDb(http.Controller):

    @http.route(
        '/saas/client/db/create',
        type='http',
        auth='none',
        metods=['POST'],
        csrf=False
    )
    @require_saas_token
    def client_db_create(self, dbname=None, demo=False, lang='en_US',
                         user_password='admin', user_login='admin',
                         country_code=None, template_dbname=None, **params):
        if not dbname:
            return bad_request(description='Missing parameter: dbname')
        _logger.info("Create database: %s (demo=%s)", dbname, demo)
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
            return server_error(description='Database not initialized.')
        return Response('OK', status=200)

    @http.route(
        '/saas/client/db/configure/base_url',
        type='http',
        auth='none',
        metods=['POST'],
        csrf=False
    )
    @require_saas_token
    @require_db_param
    def client_db_configure_base_url(self, db=None, base_url=None, **params):
        if not base_url:
            return bad_request('Base URL not provided!')

        # TODO: it seems that this url have no sense
        m = re.match(
            r"(?:(?:http|https)://)?"
            r"(?P<host>([\w\d-]+\.?)+[\w\d-]+)(?:.*)?",
            base_url)
        if not m:
            return bad_request('Wrong base URL')
        else:
            hostname = m.groupdict()['host']

        with registry(db).cursor() as cr:
            env = api.Environment(cr, SUPERUSER_ID, context={})
            env['ir.config_parameter'].set_param(
                'web.base.url', base_url)
            env['ir.config_parameter'].set_param(
                'mail.catchall.domain', hostname)
        return http.Response('OK', status=200)

    @http.route(
        '/saas/client/db/stat',
        type='http',
        auth='none',
        metods=['POST'],
        csrf=False
    )
    @require_saas_token
    @require_db_param
    def client_db_statistic(self, db=None, **params):
        data = prepare_db_statistic_data(db)
        return Response(json.dumps(data), status=200)

    @http.route(
        '/saas/client/db/users/info',
        type='http',
        auth='none',
        metods=['POST'],
        csrf=False
    )
    @require_saas_token
    @require_db_param
    def client_db_users_info(self, db=None, **params):
        """ Return list of database users
            :param db: str name of database
            :return: list of dicts [{
                'id': user_id,
                'login': user_login,
                'partner_id': user_partner_id,
                'share': True or False user_share,
                'write_uid': user_write_uid
            }]
        """
        with registry(db).cursor() as cr:
            cr.execute("""
                SELECT id, login, partner_id, share, write_uid
                FROM res_users
                WHERE active = true;
            """)
            data = cr.dictfetchall()
        return Response(json.dumps(data), status=200)
