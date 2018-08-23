import logging

from odoo import http, registry, SUPERUSER_ID
from odoo.service.db import exp_db_exist
from odoo.http import Response
from odoo.api import Environment
from ..utils import check_saas_client_token, check_db_module_state

_logger = logging.getLogger(__name__)


class OdooInfrastructureDBModuleUpgrade(http.Controller):

    @http.route(
        '/saas/client/db/module/upgrade',
        type='http',
        auth='none',
        metods=['POST'],
        csrf=False
    )
    def client_db_module_upgrade(
            self, db=None, token_hash=None, module_name=None, **params):
        result = check_saas_client_token(token_hash)
        # result is True or response (not_found, forbidden)
        if result is not True:
            return result
        if not exp_db_exist(db):
            _logger.info(
                'Database %s is not found.', db)
            return http.request.not_found()
        if module_name is None:
            _logger.info('Module name can not be None.')
            return http.request.not_found()
        state = check_db_module_state(
            db, module_name, ('installed', ))
        # state is True or response (not_found, forbidden)
        if state is not True:
            return state
        with registry(db).cursor() as cr:
            env = Environment(cr, SUPERUSER_ID, context={})
            module = env['ir.module.module'].search(
                [('name', '=', module_name)])
            module.button_immediate_upgrade()
        return Response('successfully', status=200)
