import json
from uuid import uuid4 as uuid
from datetime import datetime, timedelta

from odoo import http, registry, _, fields
from odoo.tools import config
from odoo.service.db import exp_db_exist


def _prepare_temporary_auth_data(ttl):
    ttl = ttl or 3600
    return {'token_user': str(uuid()),
            'token_password': str(uuid()),
            'expire': fields.Datetime.to_string(
                datetime.now() + timedelta(seconds=int(ttl)))}


class OdooInfrastructureAuth(http.Controller):

    @http.route(
        '/odoo/infrastructure/auth',
        type='http',
        auth='none',
        metods=['POST'],
        csrf=False
    )
    def create_temporary_login_data(self, **params):
        data = {}
        if exp_db_exist(params['db']):
            if (config.get('odoo_infrastructure_token') and
                    config.get('odoo_infrastructure_token') ==
                    params['odoo_infrastructure_token']):
                data = _prepare_temporary_auth_data(params['ttl'])
                with registry(params['db']).cursor() as cr:
                    cr.execute(
                        'INSERT INTO odoo_infrastructure_client_auth '
                        '(token_user, token_password, expire) VALUES '
                        '(%(token_user)s, %(token_password)s, %(expire)s);',
                        data
                    )
            else:
                data['error'] = _('Token does not match.')
        else:
            data['error'] = _('DB with this name is not found.')

        return json.dumps(data)
