import string
import json
import hashlib
import base64
import logging
import werkzeug

from uuid import uuid4 as uuid
from datetime import datetime, timedelta
from random import shuffle

from odoo import http, registry, _, fields
from odoo.http import request, Response
from odoo.tools import config
from odoo.service.db import exp_db_exist
from odoo import release, modules
from odoo.exceptions import AccessDenied

_logger = logging.getLogger(__name__)

SAAS_CLIENT_API_VERSION = 1
DEFAULT_TIME_TO_LOGIN = 3600
DEFAULT_LEN_TOKEN = 128


def forbidden(description=None):
    """ Shortcut for a `HTTP 403
    <https://tools.ietf.org/html/rfc7231#section-6.5.3>`_ (Forbidden)
    response
    """
    return werkzeug.exceptions.Forbidden(description)


def bad_request(description=None):
    """ Shortcut for a `HTTP 400
    <https://tools.ietf.org/html/rfc7231#section-6.5.1>`_ (BadRequest)
    response
    """
    return werkzeug.exceptions.BadRequest(description)


def generate_random_password(length):
    letters = list(string.ascii_uppercase +
                   string.ascii_lowercase +
                   string.digits) * 3
    shuffle(letters)
    return ''.join(letters[:length])


def _prepare_temporary_auth_data(ttl, db_name, token):
    ttl = ttl or DEFAULT_TIME_TO_LOGIN
    random_token = generate_random_password(DEFAULT_LEN_TOKEN)
    uri_token = '%s:%s:%s' % (db_name, random_token, token)
    uri_token = base64.b64encode(uri_token.encode("utf-8")).decode()
    return {'token_user': str(uuid()),
            'token_password': str(uuid()),
            'temp_url': '/saas_auth/%s' % uri_token,
            'expire': fields.Datetime.to_string(
                datetime.now() + timedelta(seconds=int(ttl))),
            'token_temp': random_token, }


def _prepare_saas_client_version_data():
    admin_access_url, admin_access_credentials = (
        _get_admin_access_options())
    module_version = modules.load_information_from_description_file(
        'odoo_infrastructure_client')['version'].split('.')
    # module_version is a list from the version string
    module_version_tail = '.'.join(
            module_version[-3:len(module_version)])
    # module_version_tail is a string from the last 3 version numbers

    return {
        'odoo_version': release.version,
        'odoo_version_info': release.version_info,
        'odoo_serie': release.serie,
        # receives only the last 3 version numbers
        'saas_client_version': module_version_tail,
        'saas_client_api_version': SAAS_CLIENT_API_VERSION,
        'features_enabled': {
            'admin_access_url': admin_access_url,
            'admin_access_credentials': admin_access_credentials,
        }
    }


def _check_saas_client_token(token_hash):
    """
    Returns True or correct response. Makes logging before returning a response.

    :param token_hash: hash of odoo_infrastructure_token from server
    :return: response or True
    :rtype: werkzeug.exceptions response instance or boolean
    """

    desc_no_token = 'Instance token does not exist, please configure it.'
    desc_token_not_match = 'The hashes of the tokens do not match.'

    token = config.get('odoo_infrastructure_token', False)
    if not token:
        _logger.info(desc_no_token)
        return http.request.not_found(desc_no_token)
    token_instance_hash = hashlib.sha256(token.encode('utf8')).hexdigest()
    if not token_instance_hash == token_hash:
        _logger.info(desc_token_not_match)
        return forbidden(desc_token_not_match)
    return True


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
            self, db=None, ttl=DEFAULT_TIME_TO_LOGIN,
            token_hash=None, **params):
        result = _check_saas_client_token(token_hash)
        # result is True or response (not_found, forbidden)
        if result is not True:
            return result
        admin_access_credentials = _get_admin_access_options()[1]
        if not admin_access_credentials:
            desc = '''Attempt to get temporary login/password,
            but this operation is disabled in Odoo config'''
            _logger.warning(desc)
            return forbidden(desc)
        if not exp_db_exist(db):
            _logger.info(
                'Database %s is not found.', db)
            return http.request.not_found()
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
        try:
            token = base64.b64decode(token.encode('utf-8')).decode('utf-8')
            db, token_temp, token_hash = token.split(':')
        except (base64.binascii.Error, TypeError):
            _logger.warning(
                'Bad Data: url: %s not in BASE64', token)
            return bad_request()
        result = _check_saas_client_token(token_hash)
        # result is True or response (not_found, forbidden)
        if result is not True:
            return result
        admin_access_url = _get_admin_access_options()[0]
        if not admin_access_url:
            desc = '''Attempt to login as admin via token-url,
            but this operation is disabled in Odoo config.'''
            _logger.warning(desc)
            return forbidden(desc)
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

    @http.route(
        '/saas/client/version_info',
        type='http',
        auth='none',
        metods=['POST'],
        csrf=False
    )
    def get_saas_client_version_info(self, token_hash=None, **params):
        result = _check_saas_client_token(token_hash)
        # result is True or response (not_found, forbidden)
        if result is not True:
            return result
        return Response(
            json.dumps(_prepare_saas_client_version_data()),
            status=200)
