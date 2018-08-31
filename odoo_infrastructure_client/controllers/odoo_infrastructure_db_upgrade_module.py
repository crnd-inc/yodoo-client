
import logging

from odoo import http, registry, SUPERUSER_ID
from odoo.http import Response
from odoo.api import Environment
from ..utils import (check_db_module_state,
                     require_saas_token,
                     require_db_param)

_logger = logging.getLogger(__name__)


class OdooInfrastructureDBModuleUpgrade(http.Controller):

    @http.route(
        '/saas/client/db/module/upgrade',
        type='http',
        auth='none',
        metods=['POST'],
        csrf=False
    )
    @require_saas_token
    @require_db_param
    def client_db_module_upgrade(self, db=None, module_name=None, **params):
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
