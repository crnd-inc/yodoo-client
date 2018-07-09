import string
import json
import hashlib
import base64
import logging

from uuid import uuid4 as uuid
from datetime import datetime, timedelta
from random import shuffle

from odoo import http, registry, _, fields
from odoo.http import request, Response
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
    def create_temporary_login_data(
            self, db=None, ttl=3600, token_hash=None, **params):
        if not exp_db_exist(db):
            _logger.info(
                'DB with this name: %s is not found.', db)
            return Response(
                json.dumps({'error': _('DB with this name is not found.')}),
                status=400)

        token = config.get('odoo_infrastructure_token')
        if not token:
            _logger.info(
                'Instance token: does not exist, please configure it.')
            return http.request.not_found()
        token_instance_hash = hashlib.sha256(token.encode('utf8')).hexdigest()
        if token_instance_hash != token_hash:
            _logger.info(
                'Tokens: %s and %s does not match.',
                token_instance_hash, token_hash)
            return Response(
                json.dumps({'error': _('Tokens does not match.')}),
                status=400)
        data = _prepare_temporary_auth_data(ttl, db, token_hash)
        with registry(db).cursor() as cr:
            cr.execute("""
                INSERT INTO odoo_infrastructure_client_auth
                (token_user, token_password, expire, token_temp)
                VALUES
                (%(token_user)s,
                %(token_password)s,
                %(expire)s,
                %(token_temp)s);
                """, data)
        return Response(json.dumps(data), status=200)

    @http.route(
        '/saas_auth/<token>',
        type='http',
        auth='none',
        metods=['GET'],
        csrf=False
    )
    def temporary_auth(self, token):

        try:
            token = base64.b64decode(token).decode('utf-8')
            db, token_temp, hash_token = token.split(':')
        except base64.binascii.Error:
            _logger.warning(
                'Bad Data: url: %s not in BASE64', token)
            return Response('Bad request', status=400)

        token_instance_hash = hashlib.sha256(
            config.get('odoo_infrastructure_token').encode('utf8')
        ).hexdigest()
        if hash_token != token_instance_hash:
            _logger.info(
                'Tokens: %s and %s does not match.',
                token_instance_hash, hash_token)
            return Response('Bad request', status=400)

        with registry(db).cursor() as cr:
            cr.execute("""
                SELECT id, token_user, token_password FROM
                odoo_infrastructure_client_auth
                WHERE token_temp=%s AND
                expire > CURRENT_TIMESTAMP AT TIME ZONE 'UTC';""",
                       (token_temp,))
            res = cr.fetchone()
        if not res:
            _logger.warning(
                'Temp url %s does not exist', token)
            return http.request.not_found()

        auth_id, user, password = res
        request.session.authenticate(db, user, password)
        with registry(db).cursor() as cr:
            cr.execute(
                """DELETE FROM odoo_infrastructure_client_auth
                WHERE id = %s;""", (auth_id,)
            )
        return http.redirect_with_hash('/web')
