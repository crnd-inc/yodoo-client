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


def _check_instance_token(token_hash):
    token = config.get('odoo_infrastructure_token')
    if not token:
        return None
    token_instance_hash = hashlib.sha256(token.encode('utf8')).hexdigest()
    return token_instance_hash == token_hash


def _get_admin_access_options():
    """
        Returns the admin_access options from config.
        By default this is True.
    :return: tuple of booleans
            first element: admin_access_url from config or default
            second element: admin_access_credentials from config or default
    :rtype: tuple(boolean, boolean)
    """
    return (config.get('admin_access_url', True),
            config.get('admin_access_credentials', True))


class OdooInfrastructureAuth(http.Controller):

    @http.route(
        ['/odoo/infrastructure/auth', '/saas/client/auth'],
        type='http',
        auth='none',
        metods=['POST'],
        csrf=False
    )
    def create_temporary_login_data(
            self, db=None, ttl=3600, token_hash=None, **params):
        admin_access_url, admin_access_credentials = (
            _get_admin_access_options())
        _logger.info(
            'data: %s %s', admin_access_url, admin_access_credentials)
        if not admin_access_credentials:
            _logger.info(
                'Was an attempt to get a time-old password and login')
            return Response(
                json.dumps({'error': _(
                    'The function of obtaining a temporary login '
                    'and password for access is disabled.'
                )}),
                status=403)
        checked_token = _check_instance_token(token_hash)
        if checked_token is None:
            _logger.info(
                'Instance token does not exist, please configure it.')
            return http.request.not_found()
        elif checked_token is False:
            _logger.info(
                'The hashes of the tokens do not match.')
            return Response(
                json.dumps({'error': _('Tokens does not match.')}),
                status=403)
        if not exp_db_exist(db):
            _logger.info(
                'Database %s is not found.', db)
            return Response(
                json.dumps({'error': _('DB with this name is not found.')}),
                status=404)
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
        ['/saas_auth/<token>', '/saas/client/auth/<token>'],
        type='http',
        auth='none',
        metods=['GET'],
        csrf=False
    )
    def temporary_auth(self, token):

        admin_access_url, admin_access_credentials = (
            _get_admin_access_options())
        _logger.info(
            'data auth: %s %s', admin_access_url, admin_access_credentials)
        if not admin_access_url:
            _logger.info(
                'Was an attempt to login as admin.')
            return Response('Perhaps this feature is disabled on the client.',
                            status=403)
        try:
            token = base64.b64decode(token.encode('utf-8')).decode('utf-8')
            db, token_temp, token_hash = token.split(':')
        except (base64.binascii.Error, TypeError):
            _logger.warning(
                'Bad Data: url: %s not in BASE64', token)
            return Response('Bad request', status=400)
        checked_token = _check_instance_token(token_hash)
        if checked_token is None:
            _logger.info(
                'Instance token does not exist, please configure it.')
            return http.request.not_found()
        elif checked_token is False:
            _logger.info(
                'The hashes of the tokens do not match.')
            return Response('Bad request', status=403)
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
