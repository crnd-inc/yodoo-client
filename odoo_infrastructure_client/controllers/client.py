import json
import base64
import logging

import werkzeug.exceptions

import odoo
from odoo import http, registry
from odoo.http import request, Response
from ..utils import (
    DEFAULT_TIME_TO_LOGIN,
    SAAS_CLIENT_API_VERSION,
    require_saas_token,
    require_db_param,
    check_saas_client_token,
    get_admin_access_options,
    prepare_temporary_auth_data,
)

_logger = logging.getLogger(__name__)


class SAASClient(http.Controller):

    @http.route(
        '/saas/client/version_info',
        type='http',
        auth='none',
        metods=['POST'],
        csrf=False
    )
    @require_saas_token
    def get_saas_client_version_info(self, **params):
        admin_access_url, admin_access_credentials = (
            get_admin_access_options())
        module_version_info = (
            odoo.modules.load_information_from_description_file(
                'odoo_infrastructure_client')['version'].split('.')
        )
        module_version_serie = '.'.join(module_version_info[0:2])
        module_version = '.'.join(module_version_info[-3:])

        data = {
            'odoo_version': odoo.release.version,
            'odoo_version_info': odoo.release.version_info,
            'odoo_serie': odoo.release.serie,
            'saas_client_version': module_version,
            'saas_client_serie': module_version_serie,
            'saas_client_api_version': SAAS_CLIENT_API_VERSION,
            'features_enabled': {
                'admin_access_url': admin_access_url,
                'admin_access_credentials': admin_access_credentials,
            },
        }
        return http.Response(json.dumps(data), status=200)

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
            _logger.warning(
                "Attempt to get temporary login/password, "
                "but this operation is disabled in Odoo config")
            raise werkzeug.exceptions.Forbidden(description='Feature disabled')
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
            raise werkzeug.exceptions.BadRequest()

        check_saas_client_token(token_hash)
        admin_access_url = get_admin_access_options()[0]
        if not admin_access_url:
            _logger.warning(
                "Attempt to login as admin via token-url, "
                "but this operation is disabled in Odoo config.")
            raise werkzeug.exceptions.Forbidden(
                description='Feature disabled')

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
