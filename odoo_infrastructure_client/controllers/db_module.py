import json
import logging

from odoo import http, registry, SUPERUSER_ID
from odoo.http import Response
from odoo.api import Environment

from ..utils import (
    require_saas_token,
    require_db_param,
    check_db_module_state,
    prepare_db_module_info_data,
)

_logger = logging.getLogger(__name__)


class SAASClientDbModule(http.Controller):

    @http.route(
        '/saas/client/db/module/info',
        type='http',
        auth='none',
        metods=['POST'],
        csrf=False
    )
    @require_saas_token
    @require_db_param
    def get_client_db_module_info(self, db=None, **params):
        data = prepare_db_module_info_data(db)
        return Response(json.dumps(data), status=200)

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

    @http.route(
        '/saas/client/db/module/uninstall',
        type='http',
        auth='none',
        metods=['POST'],
        csrf=False
    )
    @require_saas_token
    @require_db_param
    def client_db_module_uninstall(self, db=None, module_name=None, **params):
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
            module.button_immediate_uninstall()
        return Response('successfully', status=200)
