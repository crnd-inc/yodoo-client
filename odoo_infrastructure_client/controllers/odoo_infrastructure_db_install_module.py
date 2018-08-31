import logging

from odoo import http, registry, SUPERUSER_ID
from odoo.http import Response
from odoo.api import Environment
from ..utils import (require_saas_token,
                     require_db_param,
                     check_db_module_state)

_logger = logging.getLogger(__name__)


class OdooInfrastructureDBModuleInstall(http.Controller):

    @http.route(
        '/saas/client/db/module/install',
        type='http',
        auth='none',
        metods=['POST'],
        csrf=False
    )
    @require_saas_token
    @require_db_param
    def client_db_module_install(self, db=None, module_name=None, **params):
        if module_name is None:
            _logger.info('Module name can not be None.')
            return http.request.not_found()
        state = check_db_module_state(
            db, module_name, ('uninstalled', 'to install'))
        # state is True or response (not_found, forbidden)
        if state is not True:
            return state
        with registry(db).cursor() as cr:
            env = Environment(cr, SUPERUSER_ID, context={})
            module = env['ir.module.module'].search(
                [('name', '=', module_name)])
            module.button_immediate_install()
        return Response('successfully', status=200)
