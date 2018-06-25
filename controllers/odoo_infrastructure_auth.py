import string
import json

from uuid import uuid4 as uuid
from datetime import datetime, timedelta
from random import shuffle

from odoo import http, registry, _, fields
from odoo.tools import config
from odoo.service.db import exp_db_exist


def generate_random_password(length):
    letters = list(string.ascii_uppercase +
                   string.ascii_lowercase +
                   string.digits) * 3
    shuffle(letters)
    return ''.join(letters[:length])


def _prepare_temporary_auth_data(ttl, db_name, token):
    ttl = ttl or 3600
    return {'token_user': str(uuid()),
            'token_password': str(uuid()),
            'token_temp': '/saas_auth:%s:%s:%s' % (
                db_name, generate_random_password(128), token),
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
                data = _prepare_temporary_auth_data(
                    params['ttl'],
                    params['db'],
                    params['odoo_infrastructure_token'])
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
