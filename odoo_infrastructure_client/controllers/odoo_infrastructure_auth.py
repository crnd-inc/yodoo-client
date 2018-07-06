import string
import json
import hashlib
import base64
import logging

from uuid import uuid4 as uuid
from datetime import datetime, timedelta
from random import shuffle

from odoo import http, registry, _, fields
from odoo.http import request
from odoo.tools import config
from odoo.service.db import exp_db_exist

_logger = logging.getLogger(__name__)


def generate_random_password(length):
    letters = list(string.ascii_uppercase +
                   string.ascii_lowercase +
                   string.digits) * 3
    shuffle(letters)
    return ''.join(letters[:length])


def _prepare_temporary_auth_data(ttl, db_name, token):
    ttl = ttl or 3600
    random_password = generate_random_password(128)
    uri_token = '%s:%s:%s' % (db_name, random_password, token)
    uri_token = base64.b64encode(uri_token.encode("utf-8")).decode()
    return {'token_user': str(uuid()),
            'token_password': str(uuid()),
            'temp_url': '/saas_auth/%s' % uri_token,
            'expire': fields.Datetime.to_string(
                datetime.now() + timedelta(seconds=int(ttl))),
            'token_temp': random_password, }


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
                    hashlib.sha256(
                        config.get('odoo_infrastructure_token').encode('utf8')
                    ).hexdigest() ==
                    params['odoo_infrastructure_token']):
                data = _prepare_temporary_auth_data(
                    params['ttl'],
                    params['db'],
                    params['odoo_infrastructure_token'])
                status_code = 200
                with registry(params['db']).cursor() as cr:
                    cr.execute(
                        'INSERT INTO odoo_infrastructure_client_auth '
                        '(token_user, token_password, expire, token_temp) '
                        'VALUES '
                        '(%(token_user)s,'
                        ' %(token_password)s,'
                        ' %(expire)s,'
                        ' %(token_temp)s);',
                        data
                    )
            else:
                _logger.info(
                    'Token: %s does not match.',
                    params['odoo_infrastructure_token'])
                data['error'] = _('Token does not match.')
                status_code = 404
        else:
            _logger.info(
                'DB with this name: %s is not found.', params['db'])
            data['error'] = _('DB with this name is not found.')
            status_code = 404
        response = request.make_response(json.dumps(data))
        response.status_code = status_code
        return response

    @http.route(
        '/saas_auth/<token>',
        type='http',
        auth='none',
        metods=['GET'],
        csrf=False
    )
    def temporary_auth(self, token):
        if len(token) % 4 == 0:
            token = base64.b64decode(token).decode('utf-8')
            db, token_temp, hash_token = token.split(':')

            if hash_token == hashlib.sha256(
                    config.get('odoo_infrastructure_token').encode('utf8')
            ).hexdigest():

                with registry(db).cursor() as cr:
                    cr.execute(
                        "SELECT id, token_user, token_password FROM"
                        " odoo_infrastructure_client_auth"
                        " WHERE token_temp=%s AND"
                        " expire > CURRENT_TIMESTAMP AT TIME ZONE 'UTC';",
                        (token_temp,)
                    )
                    res = cr.fetchone()
                if res:
                    auth_id, user, password = res
                    request.session.authenticate(db, user, password)
                    with registry(db).cursor() as cr:
                        cr.execute(
                            'DELETE FROM odoo_infrastructure_client_auth '
                            'WHERE id = %s;', (auth_id,)
                        )
                    return http.redirect_with_hash('/web')
                else:
                    _logger.warning(
                        'Temp url %s does not exist', token)
            else:
                _logger.warning(
                    'Bad Data: '
                    'dbname: %s, or token_temp: %s, or hash_token: %s',
                    db, token_temp, hash_token)
        else:
            _logger.warning(
                'Bad Data: url: %s not in BASE64', token)
        response = request.make_response('Bad request')
        response.status_code = 404
        return response
