import json
import base64
import logging

from odoo import http, registry
from odoo.http import request, Response
from ..utils import (DEFAULT_TIME_TO_LOGIN,
                     require_saas_token,
                     require_db_param,
                     check_saas_client_token,
                     get_admin_access_options,
                     forbidden,
                     bad_request,
                     prepare_temporary_auth_data,
                     prepare_saas_client_version_data)

_logger = logging.getLogger(__name__)


class OdooInfrastructureAuth(http.Controller):

    @http.route(
        ['/odoo/infrastructure/auth', '/saas/client/auth'],
        type='http',
        auth='none',
        metods=['POST'],
        csrf=False
    )
    @require_saas_token
    @require_db_param
    def create_temporary_login_data(
            self, db=None, ttl=DEFAULT_TIME_TO_LOGIN,
            token_hash=None, **params):
        admin_access_credentials = get_admin_access_options()[1]
        if not admin_access_credentials:
            desc = '''Attempt to get temporary login/password,
            but this operation is disabled in Odoo config'''
            _logger.warning(desc)
            return forbidden(desc)
        data = prepare_temporary_auth_data(ttl, db, token_hash)
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
        result = check_saas_client_token(token_hash)
        # result is True or response (not_found, forbidden)
        if result is not True:
            return result
        admin_access_url = get_admin_access_options()[0]
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
                'Temp url %s does not exist.', token)
            return forbidden('Temp url does not exist.')

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
    @require_saas_token
    def get_saas_client_version_info(self, **params):
        return Response(
            json.dumps(prepare_saas_client_version_data()),
            status=200)
